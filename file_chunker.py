def chunk_file(file_path, chunk_size=512):
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk
