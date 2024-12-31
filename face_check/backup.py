import os
import cv2
import threading
from tkinter import Tk, Label, Button, filedialog, messagebox, ttk
from deepface import DeepFace

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
def identificar_pessoas(imagem_grupo, banco_pessoas, callback):
    imagem = cv2.imread(imagem_grupo)
    if imagem is None:
        raise ValueError(f"Erro ao carregar a imagem: {imagem_grupo}")
    
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = detector.detectMultiScale(imagem, scaleFactor=1.1, minNeighbors=7, minSize=(50, 50))
    
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
        except Exception as e:
            print(f"Erro ao processar uma face: {e}")

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

        # Label para exibir mensagem de "Em Processamento"
        self.processing_label = Label(master, text="", fg="blue")
        self.processing_label.pack(pady=10)

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
            # Exibir "Em processamento"
            self.processing_label.config(text="Em processamento...")

            pasta_pessoas = filedialog.askdirectory(title="Selecione a pasta de pessoas cadastradas")
            if not pasta_pessoas:
                messagebox.showwarning("Atenção", "Nenhuma pasta selecionada.")
                self.processing_label.config(text="")  # Limpar a mensagem
                return

            imagem_grupo = filedialog.askopenfilename(title="Selecione a imagem do grupo", filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
            if not imagem_grupo:
                messagebox.showwarning("Atenção", "Nenhuma imagem selecionada.")
                self.processing_label.config(text="")  # Limpar a mensagem
                return

            self.table.delete(*self.table.get_children())
            self.pessoas_encontradas.clear()
            self.total_pessoas = 0
            self.total_label.config(text="Total de pessoas identificadas: 0")

            banco_pessoas = carregar_pessoas_cadastradas(pasta_pessoas)
            identificar_pessoas(imagem_grupo, banco_pessoas, self.atualizar_tabela)

            # Após terminar, remover a mensagem "Em processamento"
            self.processing_label.config(text="")

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
            self.processing_label.config(text="")  # Limpar a mensagem em caso de erro

# Execução do programa
if __name__ == "__main__":
    root = Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
