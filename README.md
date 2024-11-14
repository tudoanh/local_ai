# Local AI

### Goals

1. Local first
2. Minimalist
3. Open Source

### Features

1. Upload and turn files into RAG using sqlite-vec and llama-index + llamafile
2. The chat will use langchain for the LLM

### Tutorial

1. First download the Llama-3.2-3B-Instruct.Q6_K and mxbai-embed-large-v1-f16 models

`wget 'https://huggingface.co/Mozilla/mxbai-embed-large-v1-llamafile/resolve/main/mxbai-embed-large-v1-f16.llamafile' --content-disposition`

`wget 'https://huggingface.co/Mozilla/Llama-3.2-3B-Instruct-llamafile/resolve/main/Llama-3.2-3B-Instruct.Q6_K.llamafile' --content-disposition`

2. Run the models

`sh -c "sh ./Llama-3.2-3B-Instruct.Q6_K.llamafile -ngl 99 --host 0.0.0.0"`

`sh -c "sh ./mxbai-embed-large-v1-f16.llamafile -ngl 99 --port 8888 --host 0.0.0.0 --nobrowser --embedding"`

3. Run the server

`python manage.py migrate`

`python manage.py runserver`

4. Create admin account

`python manage.py createsuperuser`

5. Done

Go to http://localhost:8000/admin and login with the admin account you created, you will see all of data there. No magic behind.

Then go to http://localhost:8000/ and you will see the chat interface. Upload file and try your chatbot.
