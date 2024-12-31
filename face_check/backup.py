import os
import cv2
import threading
import sqlite3
from tkinter import Tk, Label, Button, filedialog, messagebox, ttk, Entry
from deepface import DeepFace
import re  # Para validação do formato de data

# Função para carregar as imagens cadastradas e extrair embeddings
def carregar_pessoas_cadastradas(pasta_pessoas):
    banco_pessoas = {}
    for arquivo in os.listdir(pasta_pessoas):
        caminho_imagem = os.path.join(pasta_pessoas, arquivo)
        if os.path.isfile(caminho_imagem):
            nome_pessoa = os.path.splitext(arquivo)[0]
            try:
                banco_pessoas[nome_pessoa] = {
                    'nome': nome_pessoa,
                    'path': caminho_imagem,
                    'imagem': cv2.imread(caminho_imagem)
                }
            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}")
    return banco_pessoas

# Função para identificar pessoas na imagem de entrada
def identificar_pessoas(imagem_grupo, banco_pessoas, callback, update_progress):
    imagem = cv2.imread(imagem_grupo)
    if imagem is None:
        raise ValueError(f"Erro ao carregar a imagem: {imagem_grupo}")
    
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = detector.detectMultiScale(imagem, scaleFactor=1.1, minNeighbors=7, minSize=(50, 50))
    
    total_faces = len(faces)
    processed_faces = 0

    for (x, y, w, h) in faces:
        try:
            face = imagem[y:y+h, x:x+w]
            face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            temp_face_path = "temp_face.jpg"
            cv2.imwrite(temp_face_path, cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR))
            imagem_face = cv2.imread(temp_face_path)
            
            for pessoa in banco_pessoas:
                resultado_verificacao = DeepFace.verify(banco_pessoas[pessoa]['imagem'], imagem_face, enforce_detection=False)
                if resultado_verificacao['verified']:
                    callback(pessoa)
                    break
            os.remove(temp_face_path)

            # Atualizar a barra de progresso
            processed_faces += 1
            update_progress(processed_faces / total_faces * 100)
        except Exception as e:
            print(f"Erro ao processar uma face: {e}")

# Função para salvar os dados no banco de dados
def salvar_no_banco(pessoas_encontradas, data):
    try:
        conn = sqlite3.connect('reconhecimento_facial.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS identificacoes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            pessoa TEXT,
                            data TEXT)''')

        for pessoa in pessoas_encontradas:
            cursor.execute('INSERT INTO identificacoes (pessoa, data) VALUES (?, ?)', (pessoa, data))

        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao salvar os dados: {e}")

# Função para validar o formato de data (DD-MM-YYYY)
def validar_data(data):
    # Expressão regular para validar o formato DD-MM-YYYY
    padrao_data = r"^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-\d{4}$"
    return re.match(padrao_data, data) is not None

# Interface gráfica usando Tkinter com Threads
class FaceRecognitionApp:
    def __init__(self, master):
        self.master = master
        master.title("Reconhecimento Facial")
        master.geometry("800x600")

        self.label = Label(master, text="Clique no botão para processar a imagem.")
        self.label.pack(pady=10)

        self.process_button = Button(master, text="Selecionar Imagem", command=self.processar_imagem_thread)
        self.process_button.pack(pady=10)

        self.total_label = Label(master, text="Total de pessoas identificadas: 0")
        self.total_label.pack(pady=10)

        self.table = ttk.Treeview(master, columns=("Pessoa"), show="headings")
        self.table.heading("Pessoa", text="Pessoa Identificada")
        self.table.pack(pady=20, fill="both", expand=True)

        self.pessoas_encontradas = []
        self.total_pessoas = 0

        # Barra de progresso
        self.progress_label = Label(master, text="Progresso")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(master, length=400, mode="determinate", maximum=100)
        self.progress_bar.pack(pady=10)

        # Campo para entrada da data
        self.data_label = Label(master, text="Data (Formato: DD-MM-YYYY):")
        self.data_label.pack(pady=5)

        self.data_entry = Entry(master)
        self.data_entry.pack(pady=5)

        # Botão para salvar no banco de dados
        self.save_button = Button(master, text="Salvar Dados", command=self.salvar_dados)
        self.save_button.pack(pady=10)

    def atualizar_tabela(self, pessoa):
        if pessoa not in self.pessoas_encontradas:
            self.pessoas_encontradas.append(pessoa)
            self.total_pessoas += 1
            self.table.insert("", "end", values=(pessoa,))
            self.total_label.config(text=f"Total de pessoas identificadas: {self.total_pessoas}")

    def processar_imagem_thread(self):
        thread = threading.Thread(target=self.processar_imagem)
        thread.start()

    def processar_imagem(self):
        try:
            # Iniciar a barra de progresso
            self.progress_bar.config(value=0)

            pasta_pessoas = filedialog.askdirectory(title="Selecione a pasta de pessoas cadastradas")
            if not pasta_pessoas:
                messagebox.showwarning("Atenção", "Nenhuma pasta selecionada.")
                return

            imagem_grupo = filedialog.askopenfilename(title="Selecione a imagem do grupo", filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
            if not imagem_grupo:
                messagebox.showwarning("Atenção", "Nenhuma imagem selecionada.")
                return

            self.table.delete(*self.table.get_children())
            self.pessoas_encontradas.clear()
            self.total_pessoas = 0
            self.total_label.config(text="Total de pessoas identificadas: 0")

            banco_pessoas = carregar_pessoas_cadastradas(pasta_pessoas)

            # Passando a função de atualização da barra de progresso
            identificar_pessoas(imagem_grupo, banco_pessoas, self.atualizar_tabela, self.atualizar_progresso)

            # Ao terminar, garantir que a barra chegue a 100%
            self.progress_bar.config(value=100)

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    def atualizar_progresso(self, percentagem):
        # Atualiza a barra de progresso
        self.progress_bar.config(value=percentagem)

    def salvar_dados(self):
        # Obter a data informada pelo usuário
        data = self.data_entry.get()
        
        if not data:
            messagebox.showwarning("Atenção", "Por favor, informe a data.")
            return
        
        if not validar_data(data):
            messagebox.showwarning("Atenção", "A data informada não está no formato correto. Use DD-MM-YYYY.")
            return

        # Salvar no banco de dados
        salvar_no_banco(self.pessoas_encontradas, data)

# Execução do programa
if __name__ == "__main__":
    root = Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
