#pragma comment(lib, "hdl.lib")

#include "haptics.h"
#include <windows.h>
#include <math.h>

// Continuous servo callback function
HDLServoOpExitCode ContactCB(void* pUserData)
{
    // Get pointer to haptics object
    HapticsClass* haptics = static_cast< HapticsClass* >( pUserData );

    // Get current state of haptic device
    hdlToolPosition(haptics->m_positionServo);
    hdlToolButton(&(haptics->m_buttonServo));

    // Call the function that does the heavy duty calculations.
    haptics->BrailleContact();

    // Send forces to device
    hdlSetToolForce(haptics->m_forceServo);

    // Make sure to continue processing
    return HDL_SERVOOP_CONTINUE;
}

// On-demand synchronization callback function
HDLServoOpExitCode GetStateCB(void* pUserData)
{
    // Get pointer to haptics object
    HapticsClass* haptics = static_cast< HapticsClass* >( pUserData );

    // Call the function that copies data between servo side 
    // and client side
    haptics->synch();

    // Only do this once.  The application will decide when it
    // wants to do it again, and call CreateServoOp with
    // bBlocking = true
    return HDL_SERVOOP_EXIT;
}

// Constructor--just make sure needed variables are initialized.
HapticsClass::HapticsClass()
    : m_lastFace(FACE_NONE),
      m_deviceHandle(HDL_INVALID_HANDLE),
      m_servoOp(HDL_INVALID_HANDLE),
      m_cubeEdgeLength(1),
      m_cubeStiffness(1),
      m_inited(false)
{
    for (int i = 0; i < 3; i++)
        m_positionServo[i] = 0;
}

// Destructor--make sure devices are uninited.
HapticsClass::~HapticsClass()
{
    uninit();
}



int HapticsClass::init(double a_cubeSize, double a_stiffness)
{
    m_cubeEdgeLength = a_cubeSize;
    m_cubeStiffness = a_stiffness;


    HDLError err = HDL_NO_ERROR;

    // Passing "DEFAULT" or 0 initializes the default device based on the
    // [DEFAULT] section of HDAL.INI.   The names of other sections of HDAL.INI
    // could be passed instead, allowing run-time control of different devices
    // or the same device with different parameters.  See HDAL.INI for details.
    m_deviceHandle = hdlInitNamedDevice("DEFAULT");
    testHDLError("hdlInitDevice");

    if (m_deviceHandle == HDL_INVALID_HANDLE)
    {
        //MessageBox(NULL, "Could not open device", "Device Failure", MB_OK);
        return -1;
    }

    // Now that the device is fully initialized, start the servo thread.
    // Failing to do this will result in a non-funtional haptics application.
    hdlStart();
    testHDLError("hdlStart");

    // Set up callback function
    m_servoOp = hdlCreateServoOp(ContactCB, this, bNonBlocking);
    if (m_servoOp == HDL_INVALID_HANDLE)
    {
        //MessageBox(NULL, "Invalid servo op handle", "Device Failure", MB_OK);
		return -2;
    }
    testHDLError("hdlCreateServoOp");

    // Make the device current.  All subsequent calls will
    // be directed towards the current device.
    hdlMakeCurrent(m_deviceHandle);
    testHDLError("hdlMakeCurrent");

    // Get the extents of the device workspace.
    // Used to create the mapping between device and application coordinates.
    // Returned dimensions in the array are minx, miny, minz, maxx, maxy, maxz
    //                                      left, bottom, far, right, top, near)
    // Right-handed coordinates:
    //   left-right is the x-axis, right is greater than left
    //   bottom-top is the y-axis, top is greater than bottom
    //   near-far is the z-axis, near is greater than far
    // workspace center is (0,0,0)
    hdlDeviceWorkspace(m_workspaceDims);
    testHDLError("hdlDeviceWorkspace");


    // Establish the transformation from device space to app space
    // To keep things simple, we will define the app space units as
    // inches, and set the workspace to approximate the physical
    // workspace of the Falcon.  That is, a 4" cube centered on the
    // origin.  Note the Z axis values; this has the effect of
    // moving the origin of world coordinates toward the base of the
    // unit.
    m_gameWorkspace[0] = m_gameWorkspace[1] = m_gameWorkspace[2] = -2;
	m_gameWorkspace[3] = m_gameWorkspace[4] = 2;
	m_gameWorkspace[5] = 3; 

    bool useUniformScale = true;
    hdluGenerateHapticToAppWorkspaceTransform(m_workspaceDims,
                                              m_gameWorkspace,
                                              useUniformScale,
                                              m_transformMat);
    testHDLError("hdluGenerateHapticToAppWorkspaceTransform");


    m_inited = true;
	m_BrailleTextReady = false;
	m_Elementos = NULL;
	m_numElementos = 0;
	return 1;
}

// uninit() undoes the setup in reverse order.  Note the setting of
// handles.  This prevents a problem if uninit() is called
// more than once.
void HapticsClass::uninit()
{
    if (m_servoOp != HDL_INVALID_HANDLE)
    {
        hdlDestroyServoOp(m_servoOp);
        m_servoOp = HDL_INVALID_HANDLE;
    }
    hdlStop();
    if (m_deviceHandle != HDL_INVALID_HANDLE)
    {
        hdlUninitDevice(m_deviceHandle);
        m_deviceHandle = HDL_INVALID_HANDLE;
    }
    m_inited = false;
}

// This is a simple function for testing error returns.  A production
// application would need to be more sophisticated than this.
void HapticsClass::testHDLError(const char* str)
{
    HDLError err = hdlGetError();
    if (err != HDL_NO_ERROR)
    {
        //MessageBox(NULL, str, "HDAL ERROR", MB_OK);
        abort();
    }
}

// This is the entry point used by the application to synchronize
// data access to the device.  Using this function eliminates the 
// need for the application to worry about threads.
void HapticsClass::synchFromServo()
{
    hdlCreateServoOp(GetStateCB, this, bBlocking);
}

// GetStateCB calls this function to do the actual data movement.
void HapticsClass::synch()
{
    // m_positionApp is set in cubeContact().
    m_buttonApp = m_buttonServo;
}

// A utility function to handle matrix multiplication.  A production application
// would have a full vector/matrix math library at its disposal, but this is a
// simplified example.
void HapticsClass::vecMultMatrix(double srcVec[3], double mat[16], double dstVec[3])
{
    dstVec[0] = mat[0] * srcVec[0] 
        + mat[4] * srcVec[1]
        + mat[8] * srcVec[2]
        + mat[12];
    
    dstVec[1] = mat[1] * srcVec[0]
        + mat[5] * srcVec[1]
        + mat[9] * srcVec[2]
        + mat[13];

    dstVec[2] = mat[2] * srcVec[0]
        + mat[6] * srcVec[1]
        + mat[10] * srcVec[2]
        + mat[14];
}

// Here is where the heavy calculations are done.  This function is
// called from ContactCB to calculate the forces based on current
// cursor position and cube dimensions.  A simple spring model is
// used.
void HapticsClass::cubeContact()
{
    // Convert from device coordinates to application coordinates.
    vecMultMatrix(m_positionServo, m_transformMat, m_positionApp);

    m_forceServo[0] = 0; 
    m_forceServo[1] = 0; 
    m_forceServo[2] = 0;

    // Skip the whole thing if not initialized
    if (!m_inited) return;

    const double halfCube = m_cubeEdgeLength/2.0;

    double radiusWC = 0.0;
    double pointLC[3];

    // Get the cursor position in Local Coordinates.
    pointLC[0] = m_positionApp[0];
    pointLC[1] = m_positionApp[1];
    pointLC[2] = m_positionApp[2];

    // expand the cube faces by the radius of the tool
    // gives sphere-cube force model
    double l_size = halfCube + radiusWC;

    // compute signed distance to each face
    // distance > 0 implies tool position penetrates cube
    // according the specific face
    const int faces = 6;
    double l_distance[faces];
    l_distance[FACE_NEAR]   = l_size - pointLC[2];
    l_distance[FACE_RIGHT]  = l_size - pointLC[0];
    l_distance[FACE_FAR]    = pointLC[2] + l_size;
    l_distance[FACE_LEFT]   = pointLC[0] + l_size;
    l_distance[FACE_TOP]    = l_size - pointLC[1];
    l_distance[FACE_BOTTOM] = pointLC[1] + l_size;

    // Keep track of which cube face the cursor is nearest to.
    int l_nearestFace = FACE_NONE;
    if (l_nearestFace == FACE_NONE)
    {
        l_nearestFace = FACE_NEAR;
        double l_minDistance = fabs(l_distance[FACE_NEAR]);
        for (int index = FACE_RIGHT; index <= FACE_BOTTOM; ++index)
        {
            if (fabs(l_distance[index]) < l_minDistance)
            {
                l_nearestFace = index;
                l_minDistance = fabs(l_distance[index]);
            }
        }
    }

    // have the nearest face
    // tool must be interior to the face for a collision
    if (l_distance[l_nearestFace] < 0)
    {
        m_lastFace = FACE_NONE;
        m_forceServo[0] = 0; 
        m_forceServo[1] = 0; 
        m_forceServo[2] = 0;
        return;
    }

    // We know what we need to know.  Handle one of six possibilities:
    switch (l_nearestFace)
    {
        case FACE_NEAR:
        if (fabs(pointLC[0]) < l_size && fabs(pointLC[1]) < l_size)
        {
            m_forceServo[2] = l_size - pointLC[2];
            m_lastFace = l_nearestFace;
        }
        break;

        case FACE_FAR:
        if (fabs(pointLC[0]) < l_size && fabs(pointLC[1]) < l_size)
        {
            m_forceServo[2] = -l_size - pointLC[2];
            m_lastFace = l_nearestFace;
        }
        break;
        
        case FACE_RIGHT:
        if (fabs(pointLC[1]) < l_size && fabs(pointLC[2]) < l_size)
        {
            m_forceServo[0] = l_size - pointLC[0];
            m_lastFace = l_nearestFace;
            break;
        }
        break;
        
        case FACE_LEFT:
        if (fabs(pointLC[1]) < l_size && fabs(pointLC[2]) < l_size)
        {
            m_forceServo[0] = -l_size - pointLC[0];
            m_lastFace = l_nearestFace;
        }
        break;
        
        case FACE_TOP:
        if (fabs(pointLC[0]) < l_size && fabs(pointLC[2]) < l_size)
        {
            m_forceServo[1] = l_size - pointLC[1];
            m_lastFace = l_nearestFace;
        }
        break;
        
        case FACE_BOTTOM:
        if (fabs(pointLC[0]) < l_size && fabs(pointLC[2]) < l_size)
        {
            m_forceServo[1] = -l_size - pointLC[1];
            m_lastFace = l_nearestFace;
        }
    }

    // add spring stiffness to force effect
    m_forceServo[0] *= m_cubeStiffness;
    m_forceServo[1] *= m_cubeStiffness;
    m_forceServo[2] *= m_cubeStiffness;	
}

void HapticsClass::BrailleContact()
{
    // Convert from device coordinates to application coordinates.
    vecMultMatrix(m_positionServo, m_transformMat, m_positionApp);

    m_forceServo[0] = 0; 
    m_forceServo[1] = 0; 
    m_forceServo[2] = 0;

    // Skip the whole thing if not initialized
	if (!m_inited) return;

	stVertex fuerzaTemp,fuerzaSumada,posicionBraille,vDimensionesUniverso,vRadioXYZ,vSeparacionXYZCaracteres,vSeparacionXYZNodos;
	SetFull(vDimensionesUniverso,float(m_gameWorkspace[3]-m_gameWorkspace[0]),float(m_gameWorkspace[4]-m_gameWorkspace[1]),float(m_gameWorkspace[5]-m_gameWorkspace[2]));
	//Amplificar(vDimensionesUniverso,0.5f);

	float factorReduccion = 5;
	SetFull(vRadioXYZ,vDimensionesUniverso.x/factorReduccion,vDimensionesUniverso.y/factorReduccion,vDimensionesUniverso.z/factorReduccion);
	SetFull(vSeparacionXYZCaracteres,vDimensionesUniverso.x*2/factorReduccion,-vDimensionesUniverso.y*2/factorReduccion,vDimensionesUniverso.z*2/factorReduccion);
	SetFull(vSeparacionXYZNodos,vDimensionesUniverso.x/(2*factorReduccion),-vDimensionesUniverso.y/(2*factorReduccion),vDimensionesUniverso.z/(2*factorReduccion));

	//SetFull(posicionBraille,-vDimensionesUniverso.x/4,0.8*vDimensionesUniverso.y/2,0);
//	SetFull(posicionBraille,-vDimensionesUniverso.x/2,vDimensionesUniverso.y/2,0);
SetFull(posicionBraille,0,0,0.0f);
	
	Zero(fuerzaTemp);
	Zero(fuerzaSumada);
	// BoxGigante
		stVertex posicionCajaBase,radioCajaBase;
		SetFull(posicionCajaBase,0,0,-1.2f*abs(float(m_gameWorkspace[5])));
		SetFull(radioCajaBase,2.0f*abs(float(m_gameWorkspace[3])),2.0f*abs(float(m_gameWorkspace[4])),abs(float(m_gameWorkspace[5])));
		fuerzaSumada = cubeContact(posicionCajaBase, radioCajaBase);
		Suma(fuerzaSumada,fuerzaSumada,fuerzaTemp);
	if(m_BrailleTextReady)
	{
		// Nodos Braille
		for(register unsigned i = 0; i < m_numElementos; i++)
		{
			posicionBraille = HapticRenderCaracterBraille(fuerzaTemp,m_Elementos[i],vDimensionesUniverso,posicionBraille,vRadioXYZ,vSeparacionXYZCaracteres,vSeparacionXYZNodos);
			Suma(fuerzaSumada,fuerzaSumada,fuerzaTemp);
		}
	}
	m_forceServo[0] = fuerzaSumada.x; 
    m_forceServo[1] = fuerzaSumada.y; 
    m_forceServo[2] = fuerzaSumada.z;
};

stVertex HapticsClass::cubeContact(stVertex vCentro, stVertex vRadio)
{
	stVertex fuerzaActual;
	Zero(fuerzaActual);
    // Convert from device coordinates to application coordinates.
    vecMultMatrix(m_positionServo, m_transformMat, m_positionApp);

    // Skip the whole thing if not initialized
    if (!m_inited) return fuerzaActual;

    stVertex radiusWC;
    stVertex pointLC;
	Zero(radiusWC);
	Zero(pointLC);

    // Get the cursor position in Local Coordinates.
	pointLC.x = float(m_positionApp[0]) - vCentro.x;
	pointLC.y = float(m_positionApp[1]) - vCentro.y;
	pointLC.z = float(m_positionApp[2]) - vCentro.z;

    // expand the cube faces by the radius of the tool
    // gives sphere-cube force model
    stVertex l_size;
	Suma(l_size,vRadio,radiusWC);

    // compute signed distance to each face
    // distance > 0 implies tool position penetrates cube
    // according the specific face
    const int faces = 6;
    double l_distance[faces];
    l_distance[FACE_NEAR]   = l_size.z - pointLC.z;
    l_distance[FACE_RIGHT]  = l_size.x - pointLC.x;
    l_distance[FACE_FAR]    = pointLC.z + l_size.z;
    l_distance[FACE_LEFT]   = pointLC.x + l_size.x;
    l_distance[FACE_TOP]    = l_size.y - pointLC.y;
    l_distance[FACE_BOTTOM] = pointLC.y + l_size.y;

    // Keep track of which cube face the cursor is nearest to.
    int l_nearestFace = FACE_NONE;
    if (l_nearestFace == FACE_NONE)
    {
        l_nearestFace = FACE_NEAR;
        double l_minDistance = fabs(l_distance[FACE_NEAR]);
        for (int index = FACE_RIGHT; index <= FACE_BOTTOM; ++index)
        {
            if (fabs(l_distance[index]) < l_minDistance)
            {
                l_nearestFace = index;
                l_minDistance = fabs(l_distance[index]);
            }
        }
    }

    // have the nearest face
    // tool must be interior to the face for a collision
    if (l_distance[l_nearestFace] < 0)
    {
        m_lastFace = FACE_NONE;
		Zero(fuerzaActual);
        return fuerzaActual;
    }

    // We know what we need to know.  Handle one of six possibilities:
    switch (l_nearestFace)
    {
        case FACE_NEAR:
		if (fabs(pointLC.x) < l_size.x && fabs(pointLC.y) < l_size.y)
        {
			fuerzaActual.z = l_size.z - pointLC.z;
            m_lastFace = l_nearestFace;
        }
        break;

        case FACE_FAR:
		if (fabs(pointLC.x) < l_size.x && fabs(pointLC.y) < l_size.y)
        {
            fuerzaActual.z  = -l_size.z - pointLC.z;
            m_lastFace = l_nearestFace;
        }
        break;
        
        case FACE_RIGHT:
		if (fabs(pointLC.y) < l_size.y && fabs(pointLC.z) < l_size.z)
        {
            fuerzaActual.x = l_size.x - pointLC.x;
            m_lastFace = l_nearestFace;
            break;
        }
        break;
        
        case FACE_LEFT:
        if (fabs(pointLC.y) < l_size.y && fabs(pointLC.z) < l_size.z)
        {
            fuerzaActual.x = -l_size.x - pointLC.x;
            m_lastFace = l_nearestFace;
        }
        break;
        
        case FACE_TOP:
        if (fabs(pointLC.x) < l_size.x && fabs(pointLC.z) < l_size.z)
        {
            fuerzaActual.y = l_size.y - pointLC.y;
            m_lastFace = l_nearestFace;
        }
        break;
        
        case FACE_BOTTOM:
        if (fabs(pointLC.x) < l_size.x && fabs(pointLC.z) < l_size.z)
        {
            fuerzaActual.y = -l_size.y - pointLC.y;
            m_lastFace = l_nearestFace;
        }
    }

    // add spring stiffness to force effect
	Amplificar(fuerzaActual,float(m_cubeStiffness));
	return fuerzaActual;
}
// Interface function to get current position
void HapticsClass::getPosition(double pos[3])
{
    pos[0] = m_positionApp[0];
    pos[1] = m_positionApp[1];
    pos[2] = m_positionApp[2];

}

// Interface function to get button state.  Only one button is used
// in this application.
bool HapticsClass::isButtonDown()
{
    return m_buttonApp;
}

// For this application, the only device status of interest is the
// calibration status.  A different application may want to test for
// HDAL_UNINITIALIZED and/or HDAL_SERVO_NOT_STARTED
bool HapticsClass::isDeviceCalibrated()
{
    unsigned int state = hdlGetState();

    return ((state & HDAL_NOT_CALIBRATED) == 0);
}


stVertex HapticsClass::HapticRenderCaracterBraille(stVertex& vFuerzaResultante, int vIdentificador,stVertex vDimensionesUniverso,stVertex vPosicionActual,stVertex vRadioXYZ,stVertex vSeparacionXYZCaracteres,stVertex vSeparacionXYZNodos)
{
	stVertex nuevaPosicion;
	// Representacion binaria
	// 0 3
	// 1 4
	// 2 5

	// int X = XXXXXXXXb

	stVertex posicionRender,vFuerzaTemp;

	Zero(vFuerzaResultante);
	for(register unsigned i = 0; i < 6; i++)
	{
		bool verificacion = false;
		verificacion = (((vIdentificador & 1) && (i==0)) ||
						((vIdentificador & 2) && (i==1)) ||
						((vIdentificador & 4) && (i==2)) ||
						((vIdentificador & 8) && (i==3)) ||
						((vIdentificador & 16)&& (i==4)) || 
						((vIdentificador & 32)&& (i==5)));
		if(verificacion)
		{
			Suma(posicionRender,vPosicionActual,vRadioXYZ);

			switch(i)
			{
				case 0:
					break;
				case 1:
					posicionRender.y += 2.0f* vRadioXYZ.y + vSeparacionXYZNodos.y; 
					break;
				case 2:
					posicionRender.y += 4.0f* vRadioXYZ.y + 2.0f*vSeparacionXYZNodos.y; 
					break;
				case 3:
					posicionRender.x += 2.0f* vRadioXYZ.x + vSeparacionXYZNodos.x; 
					break;
				case 4:
					posicionRender.x += 2.0f* vRadioXYZ.x + vSeparacionXYZNodos.x; 
					posicionRender.y += 2.0f* vRadioXYZ.y + vSeparacionXYZNodos.y; 
					break;
				case 5:
					posicionRender.x += 2.0f* vRadioXYZ.x + vSeparacionXYZNodos.x; 
					posicionRender.y += 4.0f* vRadioXYZ.y + 2.0f*vSeparacionXYZNodos.y; 
					break;
				default:
					break;
			}
			HapticDrawNodoBraille(vFuerzaTemp,posicionRender,vRadioXYZ);
			Suma(vFuerzaResultante,vFuerzaResultante,vFuerzaTemp);
		}
	}
	Igualar(nuevaPosicion,vPosicionActual);
	nuevaPosicion.x += 4*vRadioXYZ.x + vSeparacionXYZNodos.x + vSeparacionXYZCaracteres.x;

	if(nuevaPosicion.x + 4*vRadioXYZ.x  + vSeparacionXYZNodos.x + vSeparacionXYZCaracteres.x >= vDimensionesUniverso.x)
	{
		nuevaPosicion.x =	0;
		nuevaPosicion.y +=	6 * vRadioXYZ.y + 2*vSeparacionXYZNodos.y + vSeparacionXYZCaracteres.y;
	} 
	return nuevaPosicion;
};

void HapticsClass::HapticDrawNodoBraille(stVertex& vFuerzaResultante, stVertex vPosicion,stVertex vRadio)
{
	vFuerzaResultante = cubeContact(vPosicion, vRadio);
};
void HapticsClass::HapticVectorBrailleUpdate(int* vElementos, unsigned vNumElementos)
{
	m_BrailleTextReady = false;
	if(m_Elementos != NULL)
	{
		m_Elementos = NULL;
	}
	if(vNumElementos < 1)
	{
		m_numElementos = 0;
	}
	else if(vElementos != NULL)
	{
		m_numElementos = vNumElementos;
		m_Elementos = new int[m_numElementos];
		for(register unsigned i = 0; i < m_numElementos; i++)
		{
			m_Elementos[i] = vElementos[i];
		}
	}

	m_BrailleTextReady = true;
};