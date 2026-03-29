#include "GL_Braille.h"


GL_Braille::GL_Braille(void)
{
	Zero(posicionBraille);
}

GL_Braille::~GL_Braille(void)
{
}

void GL_Braille::Resize(int w, int h)
{
	m_Width_Windows_main=w;
	m_Height_Windows_main=h;
	//igualar el tamaño de 1 pixel con la unidad a dibujar
	glViewport(0, 0, m_Width_Windows_main, m_Height_Windows_main);
	
	glMatrixMode( GL_PROJECTION );
	glLoadIdentity( );

	glOrtho(0,m_Width_Windows_main,0,m_Height_Windows_main,-3000,3000);

	stVertex ojo;
	SetFull(ojo,m_Width_Windows_main / 2.0f,m_Height_Windows_main / 2.0f,100.0f);
 	glPushMatrix();
		glLoadIdentity();
	
		gluLookAt(	ojo.x, ojo.y, ojo.z, 
					ojo.x, ojo.y, 0.0f,
					0.0f,  1.0f,  0.0f);
	glPopMatrix();

	glMatrixMode( GL_MODELVIEW );	// *** GL_MODELVIEW ***
	glLoadIdentity();

	vResized = true;
};

void GL_Braille::Renderizar(int* vElementos,unsigned numElementos,unsigned vX, unsigned vY,bool vReal)
{
	//limpiar pantalla (pintar del color 0=negro)
	glClearColor(0/255.0f, 0/255.0f, 0/255.0f, 1.0f);
	//limpiado buffers
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	//habilita test de profundidad
	glEnable(GL_DEPTH_TEST);
	//deshabilita las luces
	glDisable(GL_LIGHTING);
	SetFull(posicionBraille,0,vY,0);

	stVertex vDimensionesUniverso,vRadioXYZ,vSeparacionXYZCaracteres,vSeparacionXYZNodos;
	SetFull(vDimensionesUniverso,vX,vY,0);

	float factorReduccion = 10;
	SetFull(vRadioXYZ,vDimensionesUniverso.x/factorReduccion,-vDimensionesUniverso.y/factorReduccion,vDimensionesUniverso.z/factorReduccion);
	SetFull(vSeparacionXYZCaracteres,vDimensionesUniverso.x*2/factorReduccion,-vDimensionesUniverso.y*2/factorReduccion,vDimensionesUniverso.z*2/factorReduccion);
	SetFull(vSeparacionXYZNodos,vDimensionesUniverso.x/(2*factorReduccion),-vDimensionesUniverso.y/(2*factorReduccion),vDimensionesUniverso.z/(2*factorReduccion));

	for(register unsigned i = 0; i < numElementos; i++)
	{
		posicionBraille = RenderCaracterBraille(vElementos[i],vDimensionesUniverso,posicionBraille,vRadioXYZ,vSeparacionXYZCaracteres,vSeparacionXYZNodos);
	}
	//glFlush();

	SwapBuffers(hdc);
};
void GL_Braille::Renderizar(int vElemento,unsigned vX, unsigned vY,bool vReal)
{
	if(vResized)
	{
		//limpiar pantalla (pintar del color 0=negro)
		glClearColor(0/255.0f, 0/255.0f, 0/255.0f, 1.0f);
		//limpiado buffers
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
		//habilita test de profundidad
		glEnable(GL_DEPTH_TEST);
		//deshabilita las luces
		glDisable(GL_LIGHTING);
		SetFull(posicionBraille,0,vY/2,0);
	}

	stVertex vDimensionesUniverso,vRadioXYZ,vSeparacionXYZCaracteres,vSeparacionXYZNodos;
	SetFull(vDimensionesUniverso,vX,vY,0);
	SetFull(vRadioXYZ,5,-5,5);
	SetFull(vSeparacionXYZCaracteres,5,-5,5);
	SetFull(vSeparacionXYZNodos,2,-2,2);

	posicionBraille = RenderCaracterBraille(vElemento,vDimensionesUniverso,posicionBraille,vRadioXYZ,vSeparacionXYZCaracteres,vSeparacionXYZNodos);
	//glFlush();

	SwapBuffers(hdc);
};

stVertex GL_Braille::RenderCaracterBraille(int vIdentificador,stVertex vDimensionesUniverso,stVertex vPosicionActual,stVertex vRadioXYZ,stVertex vSeparacionXYZCaracteres,stVertex vSeparacionXYZNodos)
{
	stVertex nuevaPosicion;
	// Representacion binaria
	// 0 3
	// 1 4
	// 2 5

	// int X = XXXXXXXXb

	stVertex posicionRender;
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
					posicionRender.y += 4.0f* vRadioXYZ.y + 2.0*vSeparacionXYZNodos.y; 
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
					posicionRender.y += 4.0f* vRadioXYZ.y + 2.0*vSeparacionXYZNodos.y; 
					break;
				default:
					break;
			}
			DrawNodoBraille(posicionRender,vRadioXYZ);
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

void GL_Braille::DrawNodoBraille(stVertex vPosicion,stVertex vRadio)
{
	register float colorGris;

	glPointSize(abs(vRadio.x));

	glBegin(GL_POINTS);

		colorGris = 1.0f;
		glColor3f(colorGris,colorGris,colorGris);
		glVertex3f((float)vPosicion.x,(float)vPosicion.y, (float) vPosicion.z);
	glEnd();
}