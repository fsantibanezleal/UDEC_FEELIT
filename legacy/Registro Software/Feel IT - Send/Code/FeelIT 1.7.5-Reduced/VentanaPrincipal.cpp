#include "GL_Braille.h"
#include "VentanaPrincipal.h"
#include "haptics.h"
#include <sstream>
#include <string>
using namespace std;

using namespace FeelIT;
using namespace System;
using namespace System::IO;
using namespace System::Windows::Forms;

GL_Braille ventanaBrailleGlCentral;
int posicionActual,estadoHaptica,dimX,dimY,numElementos;
int *elementosBraille,*elementoActual;
char *elementosNormal;

// The haptics object, with which we must interact
HapticsClass gHaptics;
// Cube parameters
const double gStiffness = 100.0;
const double gCubeEdgeLength = 0.7;
int TextWindow = 40;
int distX = 8;

int Caracter2BrailleInt(wchar_t vCaracter);
int Caracter2BrailleInt(wchar_t vCaracter)
{
	register int intRepresentacion;
	switch(vCaracter)
	{
		case 'a':
		case 'A':
		case 'á':
		case 'ä':
		case 'à':
		case 'â':
		case '1':
			intRepresentacion = 1;
			break;
		case 'b':
		case 'B':
		case '2':
			intRepresentacion = 3;
			break;
		case 'c':
		case 'C':
		case '3':
			intRepresentacion = 9;
			break;
		case 'd':
		case 'D':
		case '4':
			intRepresentacion = 25;
			break;
		case 'e':
		case 'E':
		case 'é':
		case 'ë':
		case 'è':
		case 'ê':
		case '5':
			intRepresentacion = 17;
			break;
		case 'f':
		case 'F':
		case '6':
			intRepresentacion = 11;
			break;
		case 'g':
		case 'G':
		case '7':
			intRepresentacion = 27;
			break;
		case 'h':
		case 'H':
		case '8':
			intRepresentacion = 19;
			break;
		case 'i':
		case 'I':
		case 'í':
		case 'ì':
		case 'î':
		case 'ï':
		case '9':
			intRepresentacion = 10;
			break;
		case 'j':
		case 'J':
		case '0':
			intRepresentacion = 26;
			break;
		case 'k':
		case 'K':
			intRepresentacion = 5;
			break;
		case 'l':
		case 'L':
			intRepresentacion = 7;
			break;
		case 'm':
		case 'M':
			intRepresentacion = 13;
			break;
		case 'o':
		case 'O':
		case 'ö':
		case 'ô':
		case 'ò':
		case 'ó':
			intRepresentacion = 21;
			break;
		case 'p':
		case 'P':
			intRepresentacion = 15;
			break;
		case 'q':
		case 'Q':
			intRepresentacion = 31;
			break;
		case 'r':
		case 'R':
			intRepresentacion = 23;
			break;
		case 's':
		case 'S':
			intRepresentacion = 14;
			break;
		case 't':
		case 'T':
			intRepresentacion = 30;
			break;
		case 'u':
		case 'U':
		case 'ú':
		case 'ù':
		case 'ü':
		case 'û':
			intRepresentacion = 37;
			break;
		case 'v':
		case 'V':
			intRepresentacion = 39;
			break;
		case 'w':
		case 'W':
			intRepresentacion = 58;
			break;
		case 'x':
		case 'X':
			intRepresentacion = 45;
			break;
		case 'y':
		case 'Y':
			intRepresentacion = 61;
			break;
		case 'z':
		case 'Z':
			intRepresentacion = 53;
			break;
		case '&':
			intRepresentacion = 47;
			break;
		case '.':
			intRepresentacion = 4;
			break;
		case '?':
		case '¿':
			intRepresentacion = 34;
			break;
		case '!':
		case '¡':
			intRepresentacion = 22;
			break;
		case ';':
			intRepresentacion = 6;
			break;
		case '(':
			intRepresentacion = 35;
			break;
		case ')':
			intRepresentacion = 28;
			break;
		case '-':
			intRepresentacion = 28;
			break;
		default:
			intRepresentacion = 36;
			break;
	}
	return intRepresentacion;
};

System::Void VentanaPrincipal::VentanaPrincipal_FormClosed(System::Object^  sender, System::Windows::Forms::FormClosedEventArgs^  e)
{
	gHaptics.uninit();
};

System::Void VentanaPrincipal::VentanaPrincipal_Load(System::Object^  sender, System::EventArgs^  e)
{
	posicionActual = 0;
	elementoActual = new int[1];
	estadoHaptica =	gHaptics.init(gCubeEdgeLength, gStiffness);

	wglMakeCurrent (NULL, NULL);
	ventanaBrailleGlCentral.Crear( reinterpret_cast<HWND> (panelBraille->Handle.ToPointer()),W_TWO);

	elementosBraille = NULL;
	dimX=panelBraille->Width;
	dimY=panelBraille->Height;
	if (ventanaBrailleGlCentral.SetActual())
	{
		ventanaBrailleGlCentral.Resize(dimX,dimY);
	}

	
	Sleep(100);
	// Tell the user what to do if the device is not calibrated
	if (estadoHaptica == 1)
	{
		if(!gHaptics.isDeviceCalibrated())
		{
			// Initializes the variables to pass to the MessageBox::Show method.
			String^ message =	"Please home the device by extending\n ... then pushing the arms all the way in. Not Homed";
			String^ caption =	"Haptic Calibration";
			MessageBoxButtons buttons = MessageBoxButtons::YesNo;
			MessageBox::Show( message, caption, buttons );
		}
	}
};

System::Void VentanaPrincipal::VentanaPrincipal_Resize(System::Object^  sender, System::EventArgs^  e)
{	
	dimX=panelBraille->Width;
	dimY=panelBraille->Height;
	if (ventanaBrailleGlCentral.SetActual())
	{
		ventanaBrailleGlCentral.Resize(dimX,dimY);
	}
};


System::Void VentanaPrincipal::VentanaPrincipal_KeyDown(System::Object^ sender, System::Windows::Forms::KeyEventArgs^ e) {
	//wchar_t elementoBraille = e->KeyChar;
	int PosBack = 0;
	int PosForward = 0;

	bool low_limit = false;
	bool upper_limit = false;

	if (ventanaBrailleGlCentral.SetActual())
	{
		//ventanaBrailleGlCentral.Renderizar(Caracter2BrailleInt(elementoBraille),dimX,dimY,true);
		if (numElementos > 0)
		{
			if ( (e->KeyCode == Keys::Left ))
			{
				posicionActual--;
				if (posicionActual < 0) posicionActual = 0;
				elementoActual[0] = elementosBraille[posicionActual];

				label2->Text = OriginalText->Substring(posicionActual, 1);

				PosBack = posicionActual - (TextWindow >> 1);
				if (PosBack < 0)
				{
					PosBack = 0;
					low_limit = true;
				}

				PosForward = posicionActual + (TextWindow >> 1);
				if (PosForward >= numElementos)
				{
					PosForward = numElementos - 1;
					upper_limit = true;
				}

				label1->Text = OriginalText->Substring(PosBack, PosForward - PosBack);

				if (low_limit)
				{
					pictureBox1->Location::set(System::Drawing::Point(PicX + distX * posicionActual, 476));
				}

			}
			if (e->KeyCode == Keys::Right)
			{
				posicionActual++;
				if (posicionActual >= numElementos) posicionActual = numElementos - 1;
				elementoActual[0] = elementosBraille[posicionActual];

				label2->Text = OriginalText->Substring(posicionActual, 1);

				PosBack = posicionActual - (TextWindow >> 1);
				if (PosBack < 0)
				{
					PosBack = 0;
					low_limit = true;
				}

				PosForward = posicionActual + (TextWindow >> 1);
				if (PosForward >= numElementos)
				{
					PosForward = numElementos - 1;
					upper_limit = true;
				}
				label1->Text = OriginalText->Substring(PosBack, PosForward - PosBack);

				if (low_limit)
				{
					pictureBox1->Location::set(System::Drawing::Point(PicX + distX * posicionActual, 476));
				}
			}
			//if (e->KeyCode == Keys::Escape)
			//{
			//	Close();
			//}
			if (estadoHaptica == 1)
			{
				// Haptic cursor position in "world coordinates"
				double cursorPosWC[3];

				/*cursorPosWC[0] = 0.0f;
				cursorPosWC[1] = 0.0f;
				cursorPosWC[2] = 0.0f;*/

				// Must synch before data is valid
				gHaptics.synchFromServo();
				gHaptics.getPosition(cursorPosWC);
				gHaptics.HapticVectorBrailleUpdate(elementoActual, 1);
			}
			ventanaBrailleGlCentral.Renderizar(elementoActual, 1, dimX, dimY, true);
		}
	}
};

System::Void VentanaPrincipal::VentanaPrincipal_KeyPress(System::Object^  sender, System::Windows::Forms::KeyPressEventArgs^  e)
{
	//wchar_t elementoBraille = e->KeyChar;
	int PosBack=0;
	int PosForward=0;

	bool low_limit = false;
	bool upper_limit = false;

	if (ventanaBrailleGlCentral.SetActual())
	{
		//ventanaBrailleGlCentral.Renderizar(Caracter2BrailleInt(elementoBraille),dimX,dimY,true);
		if(numElementos > 0 )
		{
			if(e->KeyChar == 'a')
			{
				posicionActual--;
				if(posicionActual<0) posicionActual =0;
				elementoActual[0] = elementosBraille[posicionActual];
				
				label2->Text = OriginalText->Substring(posicionActual, 1);
				
				PosBack = posicionActual - (TextWindow>>1);
				if( PosBack < 0 )
				{
					PosBack = 0;
					low_limit = true;
				}

				PosForward = posicionActual + (TextWindow>>1);
				if( PosForward >= numElementos)
				{
					PosForward = numElementos - 1;
					upper_limit = true;
				}

				label1->Text = OriginalText->Substring(PosBack, PosForward - PosBack);

				if(low_limit)
				{
					pictureBox1->Location::set(System::Drawing::Point(PicX + distX *posicionActual, 476));
				}

			}
			if(e->KeyChar == 'd')
			{
				posicionActual++;
				if(posicionActual>=numElementos) posicionActual = numElementos-1;
				elementoActual[0] = elementosBraille[posicionActual];

				label2->Text = OriginalText->Substring(posicionActual, 1);

				PosBack = posicionActual - (TextWindow>>1);
				if( PosBack < 0 )
				{
					PosBack = 0;
					low_limit = true;
				}

				PosForward = posicionActual + (TextWindow>>1);
				if(PosForward>=numElementos)
				{
					PosForward = numElementos - 1;
					upper_limit = true;
				}
				label1->Text = OriginalText->Substring(PosBack, PosForward - PosBack);

				if(low_limit)
				{
					pictureBox1->Location::set(System::Drawing::Point(PicX + distX*posicionActual, 476));
				}
			}
			if(e->KeyChar == 27)
			{
				Close();
			}
			if(estadoHaptica == 1)
			{
				// Haptic cursor position in "world coordinates"
				double cursorPosWC[3];

				/*cursorPosWC[0] = 0.0f;
				cursorPosWC[1] = 0.0f;
				cursorPosWC[2] = 0.0f;*/

				// Must synch before data is valid
				gHaptics.synchFromServo();
				gHaptics.getPosition(cursorPosWC);
				gHaptics.HapticVectorBrailleUpdate(elementoActual,1);
			}
			ventanaBrailleGlCentral.Renderizar(elementoActual,1,dimX,dimY,true);
		}
	}
};

#include <windows.h>
System::Void VentanaPrincipal::ofdLoadText_FileOk(System::Object^  sender, System::ComponentModel::CancelEventArgs^  e)
{
	if (ventanaBrailleGlCentral.SetActual())
	{
		StreamReader^ sr = gcnew StreamReader(ofdLoadText->FileName);
		String^ line;

		int numCaracteres = 0;
		while ((line = sr->ReadLine()) != nullptr)
		{
			if(numCaracteres==0)
			{
				label1->Text = line->Substring(0, (TextWindow>>1));
				label2->Text = line->Substring(0, 1);
			}
			numCaracteres += line->Length;
			
			//label2->Text->Insert(0, lines);
		}
	    sr->Close();

		if(numCaracteres == 0)
		{
			return;
		}

		if(elementosBraille != NULL)
		{
			//delete elementosBraille;
			//delete elementosNormal;
			elementosBraille = NULL;
			elementosNormal = NULL;
			numElementos = 0;
		}
		numElementos = numCaracteres;
		elementosBraille = new int[numElementos];
		elementosNormal = new char[numElementos];
		int caracterActual = 0;
		sr = gcnew StreamReader(ofdLoadText->FileName);
		while ((line = sr->ReadLine()) != nullptr)
		{
			for(register unsigned i = 0; i < unsigned(line->Length); i++)
			{
				elementosBraille[caracterActual] = Caracter2BrailleInt(line[i]);
				elementosNormal[caracterActual] = line[i];
				caracterActual++;
			}
		}
	    sr->Close();
		teststring = line;
		OriginalText = gcnew String(elementosNormal);
		delete elementosNormal;

		if (ventanaBrailleGlCentral.SetActual())
		{
			if(numElementos > 0 )
			{
				if(estadoHaptica == 1)
				{
					// Haptic cursor position in "world coordinates"
					double cursorPosWC[3];

					/*cursorPosWC[0] = 0.0f;
					cursorPosWC[1] = 0.0f;
					cursorPosWC[2] = 0.0f;*/

					// Must synch before data is valid
					gHaptics.synchFromServo();
					gHaptics.getPosition(cursorPosWC);
					gHaptics.HapticVectorBrailleUpdate(elementosBraille,numElementos);
				}
				ventanaBrailleGlCentral.Renderizar(elementosBraille,numElementos,dimX,dimY,true);
			}
		}
		ventanaBrailleGlCentral.Renderizar(elementoActual,1,dimX,dimY,true);
		pictureBox1->Location::set(System::Drawing::Point(250, 476));
		posicionActual = 0;
	}
};

System::Void VentanaPrincipal::openTextFileToolStripMenuItem2_Click(System::Object^  sender, System::EventArgs^  e)
{
	ofdLoadText->Filter = "txt files (*.txt)|*.txt";//|All files (*.*)|*.*";
	ofdLoadText->RestoreDirectory = true;

	ofdLoadText->ShowDialog();
};
void add (EventHandler^ value)
{
	int hola = 0;
	hola++;

}
void remove (EventHandler^ value)
{
	int hola = 0;
	hola = hola - 2;

}