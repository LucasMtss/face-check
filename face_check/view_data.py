import sqlite3
from tkinter import Tk, Label, Button, Entry, messagebox, ttk
from datetime import datetime

# Função para buscar no banco de dados
def buscar_no_banco(data=None, nome=None):
    try:
        conn = sqlite3.connect('reconhecimento_facial.db')
        cursor = conn.cursor()
        
        # Consulta para obter pessoa, última data e contagem de presença
        query = '''
            SELECT pessoa, MAX(data) AS ultima_data, COUNT(pessoa) AS presenca 
            FROM identificacoes
            WHERE 1=1
        '''
        params = []

        if data:
            query += ' AND data = ?'
            params.append(data)

        if nome:
            query += ' AND pessoa LIKE ?'
            params.append(f'%{nome}%')

        query += ' GROUP BY pessoa ORDER BY pessoa'

        cursor.execute(query, params)
        resultados = cursor.fetchall()

        conn.close()
        return resultados
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao consultar o banco de dados: {e}")
        return []

# Interface gráfica para visualizar os dados
class VisualizarDadosApp:
    def __init__(self, master):
        self.master = master
        master.title("Visualizar Dados de Identificação")
        master.geometry("800x600")

        self.label = Label(master, text="Buscar Identificações")
        self.label.pack(pady=10)

        # Campo de busca por nome
        self.nome_label = Label(master, text="Nome da Pessoa:")
        self.nome_label.pack(pady=5)

        self.nome_entry = Entry(master)
        self.nome_entry.pack(pady=5)

        # Campo de busca por data
        self.data_label = Label(master, text="Data (Formato: DD-MM-YYYY):")
        self.data_label.pack(pady=5)

        self.data_entry = Entry(master)
        self.data_entry.pack(pady=5)

        # Botão de busca
        self.search_button = Button(master, text="Buscar", command=self.buscar_dados)
        self.search_button.pack(pady=10)

        # Tabela para exibir os resultados
        self.table = ttk.Treeview(master, columns=("Pessoa", "Última Data", "Presença"), show="headings")
        self.table.heading("Pessoa", text="Pessoa")
        self.table.heading("Última Data", text="Última Data")
        self.table.heading("Presença", text="Presença")
        self.table.pack(pady=20, fill="both", expand=True)

    def buscar_dados(self):
        # Obter os valores dos campos de busca
        nome = self.nome_entry.get()
        data = self.data_entry.get()

        # Converter a data para o formato YYYY-MM-DD
        if data:
            try:
                data = datetime.strptime(data, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro", "A data deve estar no formato DD-MM-YYYY.")
                return

        # Buscar no banco de dados
        resultados = buscar_no_banco(data, nome)

        # Limpar a tabela
        self.table.delete(*self.table.get_children())

        if resultados:
            for resultado in resultados:
                self.table.insert("", "end", values=resultado)
        else:
            messagebox.showinfo("Sem resultados", "Nenhum dado encontrado com os critérios fornecidos.")

# Execução do programa
if __name__ == "__main__":
    root = Tk()
    app = VisualizarDadosApp(root)
    root.mainloop()
