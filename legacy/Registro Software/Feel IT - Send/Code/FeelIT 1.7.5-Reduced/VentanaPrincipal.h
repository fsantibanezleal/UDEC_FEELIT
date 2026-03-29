#pragma once


namespace FeelIT {

	using namespace System;
	using namespace System::ComponentModel;
	using namespace System::Collections;
	using namespace System::Windows::Forms;
	using namespace System::Data;
	using namespace System::Drawing;

	/// <summary>
	/// Summary for Form1
	///
	/// WARNING: If you change the name of this class, you will need to change the
	///          'Resource File Name' property for the managed resource compiler tool
	///          associated with all .resx files this class depends on.  Otherwise,
	///          the designers will not be able to interact properly with localized
	///          resources associated with this form.
	/// </summary>

	public ref class VentanaPrincipal : public System::Windows::Forms::Form
	{
	public:
		VentanaPrincipal(void)
		{
			InitializeComponent();
			//
			//TODO: Add the constructor code here
			//
			PicX = 250;
		}
	
	public:
		static event EventHandler^ Idle {
			void add (EventHandler^ value){
				int hola;
				hola=1;
			}
			void remove (EventHandler^ value){
				int chao;
				chao = 1;
			}
		}

	protected:
		/// <summary>
		/// Clean up any resources being used.
		/// </summary>
		~VentanaPrincipal()
		{
			if (components)
			{
				delete components;
			}
		}
	private: System::Windows::Forms::OpenFileDialog^  ofdLoadText;


	private: System::Windows::Forms::MenuStrip^  menuStrip1;
	private: System::Windows::Forms::ToolStripMenuItem^  openTextFileToolStripMenuItem1;
	private: System::Windows::Forms::ToolStripMenuItem^  openTextFileToolStripMenuItem2;
	private: System::Windows::Forms::Panel^  panelBraille;
	private: System::Windows::Forms::Label^  label1;
	private: System::Windows::Forms::Label^  label2;

	private: System::Windows::Forms::Label^  label3;
	private: System::Windows::Forms::Label^  label4;
	private: System::ComponentModel::BackgroundWorker^  backgroundWorker1;
	private: System::Windows::Forms::PictureBox^  pictureBox1;

	private: System::ComponentModel::IContainer^  components;
	private: System::String^ OriginalText;
	private: String^ teststring;
	private: System::Windows::Forms::ToolStripMenuItem^  aboutToolStripMenuItem;

	private: int PicX;
	private: System::Windows::Forms::Label^ label5;
	private: System::Windows::Forms::Label^ label6;
	private: int PicY;
	protected: 

	private:
		/// <summary>
		/// Required designer variable.
		/// </summary>


#pragma region Windows Form Designer generated code
		/// <summary>
		/// Required method for Designer support - do not modify
		/// the contents of this method with the code editor.
		/// </summary>
		void InitializeComponent(void)
		{
			System::ComponentModel::ComponentResourceManager^ resources = (gcnew System::ComponentModel::ComponentResourceManager(VentanaPrincipal::typeid));
			this->ofdLoadText = (gcnew System::Windows::Forms::OpenFileDialog());
			this->menuStrip1 = (gcnew System::Windows::Forms::MenuStrip());
			this->openTextFileToolStripMenuItem1 = (gcnew System::Windows::Forms::ToolStripMenuItem());
			this->openTextFileToolStripMenuItem2 = (gcnew System::Windows::Forms::ToolStripMenuItem());
			this->aboutToolStripMenuItem = (gcnew System::Windows::Forms::ToolStripMenuItem());
			this->panelBraille = (gcnew System::Windows::Forms::Panel());
			this->label1 = (gcnew System::Windows::Forms::Label());
			this->label2 = (gcnew System::Windows::Forms::Label());
			this->label3 = (gcnew System::Windows::Forms::Label());
			this->label4 = (gcnew System::Windows::Forms::Label());
			this->backgroundWorker1 = (gcnew System::ComponentModel::BackgroundWorker());
			this->pictureBox1 = (gcnew System::Windows::Forms::PictureBox());
			this->label5 = (gcnew System::Windows::Forms::Label());
			this->label6 = (gcnew System::Windows::Forms::Label());
			this->menuStrip1->SuspendLayout();
			(cli::safe_cast<System::ComponentModel::ISupportInitialize^>(this->pictureBox1))->BeginInit();
			this->SuspendLayout();
			// 
			// ofdLoadText
			// 
			this->ofdLoadText->FileName = L"openFileDialog1";
			this->ofdLoadText->Filter = L"\"txt files|*.txt\"";
			this->ofdLoadText->FileOk += gcnew System::ComponentModel::CancelEventHandler(this, &VentanaPrincipal::ofdLoadText_FileOk);
			// 
			// menuStrip1
			// 
			this->menuStrip1->Items->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(2) {
				this->openTextFileToolStripMenuItem1,
					this->aboutToolStripMenuItem
			});
			this->menuStrip1->Location = System::Drawing::Point(0, 0);
			this->menuStrip1->Name = L"menuStrip1";
			this->menuStrip1->Padding = System::Windows::Forms::Padding(4, 2, 0, 2);
			this->menuStrip1->Size = System::Drawing::Size(703, 24);
			this->menuStrip1->TabIndex = 1;
			this->menuStrip1->Text = L"menuStrip1";
			// 
			// openTextFileToolStripMenuItem1
			// 
			this->openTextFileToolStripMenuItem1->DropDownItems->AddRange(gcnew cli::array< System::Windows::Forms::ToolStripItem^  >(1) { this->openTextFileToolStripMenuItem2 });
			this->openTextFileToolStripMenuItem1->Name = L"openTextFileToolStripMenuItem1";
			this->openTextFileToolStripMenuItem1->Size = System::Drawing::Size(69, 20);
			this->openTextFileToolStripMenuItem1->Text = L"Opciones";
			// 
			// openTextFileToolStripMenuItem2
			// 
			this->openTextFileToolStripMenuItem2->Name = L"openTextFileToolStripMenuItem2";
			this->openTextFileToolStripMenuItem2->Size = System::Drawing::Size(191, 22);
			this->openTextFileToolStripMenuItem2->Text = L"Abrir Archivo de Texto";
			this->openTextFileToolStripMenuItem2->Click += gcnew System::EventHandler(this, &VentanaPrincipal::openTextFileToolStripMenuItem2_Click);
			// 
			// aboutToolStripMenuItem
			// 
			this->aboutToolStripMenuItem->Name = L"aboutToolStripMenuItem";
			this->aboutToolStripMenuItem->Size = System::Drawing::Size(52, 20);
			this->aboutToolStripMenuItem->Text = L"About";
			this->aboutToolStripMenuItem->Click += gcnew System::EventHandler(this, &VentanaPrincipal::aboutToolStripMenuItem_Click);
			// 
			// panelBraille
			// 
			this->panelBraille->Anchor = static_cast<System::Windows::Forms::AnchorStyles>(((System::Windows::Forms::AnchorStyles::Top | System::Windows::Forms::AnchorStyles::Left)
				| System::Windows::Forms::AnchorStyles::Right));
			this->panelBraille->Location = System::Drawing::Point(158, 23);
			this->panelBraille->Margin = System::Windows::Forms::Padding(2);
			this->panelBraille->Name = L"panelBraille";
			this->panelBraille->Size = System::Drawing::Size(502, 377);
			this->panelBraille->TabIndex = 2;
			// 
			// label1
			// 
			this->label1->AutoSize = true;
			this->label1->Font = (gcnew System::Drawing::Font(L"Microsoft Sans Serif", 12, System::Drawing::FontStyle::Regular, System::Drawing::GraphicsUnit::Point,
				static_cast<System::Byte>(0)));
			this->label1->Location = System::Drawing::Point(270, 420);
			this->label1->Name = L"label1";
			this->label1->Size = System::Drawing::Size(0, 20);
			this->label1->TabIndex = 3;
			// 
			// label2
			// 
			this->label2->AutoSize = true;
			this->label2->Font = (gcnew System::Drawing::Font(L"Microsoft Sans Serif", 20, System::Drawing::FontStyle::Bold, System::Drawing::GraphicsUnit::Point,
				static_cast<System::Byte>(0)));
			this->label2->Location = System::Drawing::Point(55, 111);
			this->label2->MinimumSize = System::Drawing::Size(20, 20);
			this->label2->Name = L"label2";
			this->label2->Size = System::Drawing::Size(20, 31);
			this->label2->TabIndex = 4;
			// 
			// label3
			// 
			this->label3->AutoSize = true;
			this->label3->BorderStyle = System::Windows::Forms::BorderStyle::Fixed3D;
			this->label3->Font = (gcnew System::Drawing::Font(L"Microsoft Sans Serif", 12, static_cast<System::Drawing::FontStyle>(((System::Drawing::FontStyle::Bold | System::Drawing::FontStyle::Italic)
				| System::Drawing::FontStyle::Underline)), System::Drawing::GraphicsUnit::Point, static_cast<System::Byte>(0)));
			this->label3->Location = System::Drawing::Point(12, 34);
			this->label3->Name = L"label3";
			this->label3->Size = System::Drawing::Size(133, 22);
			this->label3->TabIndex = 4;
			this->label3->Text = L"Letra en Braille";
			// 
			// label4
			// 
			this->label4->AutoSize = true;
			this->label4->BorderStyle = System::Windows::Forms::BorderStyle::Fixed3D;
			this->label4->Font = (gcnew System::Drawing::Font(L"Microsoft Sans Serif", 12, static_cast<System::Drawing::FontStyle>(((System::Drawing::FontStyle::Bold | System::Drawing::FontStyle::Italic)
				| System::Drawing::FontStyle::Underline)), System::Drawing::GraphicsUnit::Point, static_cast<System::Byte>(0)));
			this->label4->Location = System::Drawing::Point(12, 399);
			this->label4->Name = L"label4";
			this->label4->Size = System::Drawing::Size(121, 22);
			this->label4->TabIndex = 3;
			this->label4->Text = L"Texto Original";
			this->label4->Click += gcnew System::EventHandler(this, &VentanaPrincipal::Label4_Click);
			// 
			// pictureBox1
			// 
			this->pictureBox1->Image = (cli::safe_cast<System::Drawing::Image^>(resources->GetObject(L"pictureBox1.Image")));
			this->pictureBox1->Location = System::Drawing::Point(250, 476);
			this->pictureBox1->Name = L"pictureBox1";
			this->pictureBox1->Size = System::Drawing::Size(26, 56);
			this->pictureBox1->TabIndex = 5;
			this->pictureBox1->TabStop = false;
			// 
			// label5
			// 
			this->label5->AutoSize = true;
			this->label5->Font = (gcnew System::Drawing::Font(L"Microsoft Sans Serif", 12, System::Drawing::FontStyle::Regular, System::Drawing::GraphicsUnit::Point,
				static_cast<System::Byte>(0)));
			this->label5->Location = System::Drawing::Point(94, 476);
			this->label5->MinimumSize = System::Drawing::Size(100, 15);
			this->label5->Name = L"label5";
			this->label5->Size = System::Drawing::Size(100, 20);
			this->label5->TabIndex = 6;
			this->label5->Text = L"label5";
			this->label5->TextAlign = System::Drawing::ContentAlignment::TopRight;
			this->label5->Visible = false;
			// 
			// label6
			// 
			this->label6->AutoSize = true;
			this->label6->Font = (gcnew System::Drawing::Font(L"Microsoft Sans Serif", 12, System::Drawing::FontStyle::Regular, System::Drawing::GraphicsUnit::Point,
				static_cast<System::Byte>(0)));
			this->label6->Location = System::Drawing::Point(416, 476);
			this->label6->MinimumSize = System::Drawing::Size(100, 15);
			this->label6->Name = L"label6";
			this->label6->Size = System::Drawing::Size(100, 20);
			this->label6->TabIndex = 7;
			this->label6->Text = L"label6";
			this->label6->Visible = false;
			this->label6->Click += gcnew System::EventHandler(this, &VentanaPrincipal::Label6_Click);
			// 
			// VentanaPrincipal
			// 
			this->AutoScaleDimensions = System::Drawing::SizeF(6, 13);
			this->AutoScaleMode = System::Windows::Forms::AutoScaleMode::Font;
			this->ClientSize = System::Drawing::Size(703, 535);
			this->Controls->Add(this->label6);
			this->Controls->Add(this->label5);
			this->Controls->Add(this->pictureBox1);
			this->Controls->Add(this->label3);
			this->Controls->Add(this->label2);
			this->Controls->Add(this->label4);
			this->Controls->Add(this->label1);
			this->Controls->Add(this->panelBraille);
			this->Controls->Add(this->menuStrip1);
			this->MainMenuStrip = this->menuStrip1;
			this->Margin = System::Windows::Forms::Padding(2);
			this->Name = L"VentanaPrincipal";
			this->Text = L"FeelIT ... First Reborn";
			this->FormClosed += gcnew System::Windows::Forms::FormClosedEventHandler(this, &VentanaPrincipal::VentanaPrincipal_FormClosed);
			this->Load += gcnew System::EventHandler(this, &VentanaPrincipal::VentanaPrincipal_Load);
			this->KeyDown += gcnew System::Windows::Forms::KeyEventHandler(this, &VentanaPrincipal::VentanaPrincipal_KeyDown);
			this->KeyPress += gcnew System::Windows::Forms::KeyPressEventHandler(this, &VentanaPrincipal::VentanaPrincipal_KeyPress);
			this->Resize += gcnew System::EventHandler(this, &VentanaPrincipal::VentanaPrincipal_Resize);
			this->menuStrip1->ResumeLayout(false);
			this->menuStrip1->PerformLayout();
			(cli::safe_cast<System::ComponentModel::ISupportInitialize^>(this->pictureBox1))->EndInit();
			this->ResumeLayout(false);
			this->PerformLayout();

		}
#pragma endregion
	private: System::Void VentanaPrincipal_Load(System::Object^  sender, System::EventArgs^  e);
	private: System::Void VentanaPrincipal_Resize(System::Object^  sender, System::EventArgs^  e);
	private: System::Void VentanaPrincipal_KeyPress(System::Object^  sender, System::Windows::Forms::KeyPressEventArgs^  e);
	private: System::Void ofdLoadText_FileOk(System::Object^  sender, System::ComponentModel::CancelEventArgs^  e);
	private: System::Void openTextFileToolStripMenuItem2_Click(System::Object^  sender, System::EventArgs^  e);
	private: System::Void VentanaPrincipal_FormClosed(System::Object^  sender, System::Windows::Forms::FormClosedEventArgs^  e);
private: System::Void aboutToolStripMenuItem_Click(System::Object^  sender, System::EventArgs^  e) {
			 Form ^ dlg1 = gcnew Form();
			 dlg1->Text = "About";
			 
			 System::Windows::Forms::Label^  dlg_label = gcnew Label();

			 dlg_label->AutoSize::set(true);
			 dlg_label->Location = System::Drawing::Point(10, 210);
			 dlg_label->Name = L"label_dlg";
			 dlg_label->Size = System::Drawing::Size(0, 13);
			 dlg_label->TabIndex = 3;
			 dlg_label->Text = L"FeelIT";

			 System::Windows::Forms::Label^  dlg_label2 = gcnew Label();

			 dlg_label2->AutoSize::set(true);
			 dlg_label2->Location = System::Drawing::Point(15, 230);
			 dlg_label2->Name = L"label_dlg";
			 dlg_label2->Size = System::Drawing::Size(0, 13);
			 dlg_label2->TabIndex = 3;
			 dlg_label2->Text = L"Todos los derechos reservados";

			 System::Windows::Forms::PictureBox^  FeelITLogo;

			 FeelITLogo = (gcnew System::Windows::Forms::PictureBox());

			 FeelITLogo->AutoSize::set(true);
			 FeelITLogo->Location = System::Drawing::Point(10, 30);
			 FeelITLogo->Name = L"pictureBox1";
			 FeelITLogo->Load("FeelIT.jpg");
			 //FeelITLogo->Size = System::Drawing::Size(26, 56);
			 FeelITLogo->TabIndex = 5;
			 FeelITLogo->TabStop = false;

			 dlg1->Controls->Add(dlg_label);
			 dlg1->Controls->Add(dlg_label2);
			 dlg1->Controls->Add(FeelITLogo);

			 dlg1->ShowDialog();
		 }
private: System::Void Label4_Click(System::Object^ sender, System::EventArgs^ e) {
}
private: System::Void Label6_Click(System::Object^ sender, System::EventArgs^ e) {
}
private: System::Void VentanaPrincipal_KeyDown(System::Object^ sender, System::Windows::Forms::KeyEventArgs^ e);
};
}

