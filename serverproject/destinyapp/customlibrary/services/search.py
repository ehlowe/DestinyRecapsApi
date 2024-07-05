import os
import traceback

import faiss
import numpy as np

from .. import utils




async def load_vectordb(video_id):
    """
    Loads vector db from file
    """
    index_path=os.path.join("destinyapp/working_folder/vectordbs",video_id+".index")
    # actually load the vector with code in this file
    index = faiss.read_index(index_path)
    return index

async def search_vectordb(vector_db, query):
    """
    Searches given vectordb with query
    
    Returns tuple of 'D' and 'I'"""
    # Generate query embedding
    query_embedding = await utils.async_openai_client.embeddings.create(input=query,model="text-embedding-3-large")
    query_embedding_np = np.array(query_embedding.data[0].embedding).astype('float32').reshape(1, -1)
    k=vector_db.ntotal
    if k>5:
        k=5

    D, I = vector_db.search(query_embedding_np, k)
    return (D,I)

async def search(video_id, query):
    # get transcript_data
    transcript_data=await utils.get_plain_transcript(video_id)

    try:
        if transcript_data:
            # load vector db from file
            index = await load_vectordb(video_id)

            # search vector db
            d,i=await search_vectordb(index, query)

            # get index of query in transcript
            query_character_index=transcript_data.transcript.find(transcript_data.text_chunks[i[0][0]])
            all_indexes=[]
            for index_value in i[0]:
                all_indexes.append(transcript_data.transcript.find(transcript_data.text_chunks[index_value]))


            return {"index":query_character_index,"all_indexes":all_indexes}
        else:
            return {}
     # print all details for the error:
    except Exception as e:
        print("Error in search.py: ",e)
        print(traceback.format_exc())

        return {}