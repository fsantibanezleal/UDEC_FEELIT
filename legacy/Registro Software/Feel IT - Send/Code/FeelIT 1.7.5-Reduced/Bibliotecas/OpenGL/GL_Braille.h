#pragma once
#include "OGL.h"
#include "BasicFunctions.h"

class GL_Braille : public OGL
{
private:
	bool		vResized;
	stVertex	posicionBraille;
public:
	GL_Braille(void);
	~GL_Braille(void);
	virtual void Resize(int w, int h);
	void Renderizar(int vElemento,unsigned vX, unsigned vY,bool vReal);
	void Renderizar(int* vElementos,unsigned numElementos,unsigned vX, unsigned vY,bool vReal);
	stVertex RenderCaracterBraille(int vIdentificador,stVertex vDimensionesUniverso,stVertex vPosicionActual,stVertex vRadioXYZ,stVertex vSeparacionXYZCaracteres,stVertex vSeparacionXYZNodos);
	void DrawNodoBraille(stVertex vPosicion,stVertex vRadio);
};
