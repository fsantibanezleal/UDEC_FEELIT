// FeelIT.cpp : main project file.

#include "VentanaPrincipal.h"

using namespace FeelIT;

[STAThreadAttribute]
int main(array<System::String ^> ^args)
{
	// Enabling Windows XP visual effects before any controls are created
	Application::EnableVisualStyles();
	Application::SetCompatibleTextRenderingDefault(false); 

	// Create the main window and run it
	Application::Run(gcnew VentanaPrincipal());
	return 0;
}
