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

async def search_vectordb(vector_db, query, k_size=5):
    """
    Searches given vectordb with query
    
    Returns tuple of 'D' and 'I'"""
    # Generate query embedding
    query_embedding = await utils.async_openai_client.embeddings.create(input=query,model="text-embedding-3-large")
    query_embedding_np = np.array(query_embedding.data[0].embedding).astype('float32').reshape(1, -1)
    k=vector_db.ntotal
    if k>k_size:
        k=k_size

    D, I = vector_db.search(query_embedding_np, k)
    return (D,I)

async def search(video_id, query, k_size=5):
    # get transcript_data
    transcript_data=await utils.get_plain_transcript(video_id)

    try:
        if transcript_data:
            # load vector db from file
            index = await load_vectordb(video_id)

            # search vector db
            d,i=await search_vectordb(index, query, k_size=k_size)

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
    

async def all_search(query, k_size=5):
    # get all video_ids
    all_recaps=await utils.get_all_recaps_fast()

    # create dict to hold all search results
    index = await load_vectordb("master_all")

    d, i=await search_vectordb(index, query, k_size=k_size)

    filtered_recaps=[]
    for recap in all_recaps:
        if recap.get("recap", None):
            filtered_recaps.append(recap)

    all_search_results=[]
    for index_value in i[0]:
        recap=filtered_recaps[index_value].get("recap", None)
        if recap:
            all_search_results.append({"recap":filtered_recaps[index_value]["recap"], "video_id":filtered_recaps[index_value]["video_id"]})
        else:
            print("Empty Recap: ", filtered_recaps[index_value]["video_id"])
            all_search_results.append({"recap":"Empty", "video_id":None})

    return all_search_results