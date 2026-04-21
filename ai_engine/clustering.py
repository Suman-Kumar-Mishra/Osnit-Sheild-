import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


SIMILARITY_THRESHOLD = 0.75


def cluster_records(records):
    """
    records: list of RawOSINT objects with embedding
    """

    embeddings = []
    valid_records = []

    for record in records:
        if record.embedding:
            embeddings.append(record.embedding)
            valid_records.append(record)

    if not embeddings:
        return

    embeddings = np.array(embeddings)

    similarity_matrix = cosine_similarity(embeddings)

    cluster_id = 1
    assigned = set()

    for i in range(len(valid_records)):
        if i in assigned:
            continue

        valid_records[i].cluster_id = cluster_id
        assigned.add(i)

        for j in range(i + 1, len(valid_records)):
            if similarity_matrix[i][j] >= SIMILARITY_THRESHOLD:
                valid_records[j].cluster_id = cluster_id
                assigned.add(j)

        cluster_id += 1
