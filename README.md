Projeto Monitor de Bengala 

Este software é uma interface desktop feita em Python e PyQt6 para simular o monitoramento de uma bengala inteligente.

Esta versão carrega a interface do usuário a partir de um arquivo .ui (criado pelo QT Designer).

Como Configurar e Rodar

Crie um Ambiente Virtual (Recomendado):
(Você já tem uma pasta venv, então só precisa ativá-la)

Ative o Ambiente Virtual:

Windows: .\venv\Scripts\activate

macOS/Linux: source venv/bin/activate

Instale as Dependências:
(Verifique se o seu requirements.txt tem PyQt6 e PyQt6-tools)

pip install -r requirements.txt


Rode a Aplicação:

python app_designer.py


Como Editar a Interface (QT Designer)

No seu terminal (com o ambiente virtual ativado), digite designer para abrir o QT Designer.

Abra o arquivo main_window.ui para fazer alterações visuais.

Salve o arquivo.

Rode python app_designer.py novamente para ver as mudanças.