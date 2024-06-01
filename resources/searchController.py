# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# # Example sentences and their embeddings
# model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# @router.get('/search_user')
# def SearchUser(request: Request, text: str Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     user_input = input(text)
#     user_embedding = model.encode([user_input])[0]
#     job_embeddings = [model.encode([education])[0] for title in job_titles]

#     return = {search_similar_job_titles(user_embedding, job_embeddings, job_titles)}

#     similarities = cosine_similarity([query_embedding], embeddings_list)[0]
#     sorted_indices = sorted(range(len(similarities)), key=lambda x: similarities[x], reverse=True)[:top_n]
#     print(f"Top {top_n} similar job titles:")

#     for index in sorted_indices:
#         print(f"{titles_list[index]}: Similarity = {similarities[index]:.4f}")

      
        
# def search_similar_job_titles(query_embedding, embeddings_list, titles_list, top_n=3):
#     similarities = cosine_similarity([query_embedding], embeddings_list)[0]
#     # Sort the indices based on similarity and get the top N
#     sorted_indices = sorted(range(len(similarities)), key=lambda x: similarities[x], reverse=True)[:top_n]

#     print(f"Top {top_n} similar job titles:")
#     for index in sorted_indices:
#         print(f"{titles_list[index]}: Similarity = {similarities[index]:.4f}")

# # Example usage:
# user_input = input("Enter a job title: ")
# user_embedding = model.encode([user_input])[0]

# # Assuming you have a list of job titles
# job_titles = ["Data Scientist", "Software Engineer", "Product Manager", "Data Analyst", "Machine Learning Engineer"]

# # Assuming you have a list of embeddings corresponding to each job title
# job_embeddings = [model.encode([title])[0] for title in job_titles]

# # Perform similarity search
# search_similar_job_titles(user_embedding, job_embeddings, job_titles)


