import sqlite3

model_dict = {"keybert":None,
            "patternrank":None,
            "promptrank":None}

def create_connection(db_file: str):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def validate_author(conn, ssId):
    with conn:
        c = conn.cursor()
        c.execute("SELECT author_pk FROM authors WHERE author_ssid = (?)", (ssId,))
        author_pk = c.fetchone()
    return author_pk[0] if author_pk is not None else None


def get_author_data(conn, author_pk):
    with conn:
        c = conn.cursor()

        c.execute("SELECT next_page_start from authors WHERE author_pk = (?)", (author_pk,))
        start = c.fetchone()[0]

        model_list = list(model_dict.keys())
        model_pos_neg_index = [start, (start+1)%5, (start+2)%5]

        # As of now: 6 questions, 3 models, each model 1 positive and 1 negative
        # Alternatively: 8 questions, 2 models, each model 2 positive and 2 negative
        result = []
        for idx, model in enumerate(model_list):
            pn_idx = model_pos_neg_index[idx]
            for tag in [f"pos{pn_idx}", f"neg{pn_idx}"]:
                c.execute(f"""SELECT model_author_paper_pk, papers.title, keyphrases_to_show FROM model_author_paper_similarity
                    LEFT JOIN papers ON model_author_paper_similarity.paper_fk = papers.paper_pk
                    WHERE model_author_paper_similarity.author_hand_confidence IS NULL AND model_author_paper_similarity.author_fk = (?) AND papers.tag = (?) AND model_author_paper_similarity.model_name = (?)
                    """, (author_pk, tag, model,))
                result.extend(c.fetchall())
    return result


def store_contribute(conn, author_pk, contribute_response):
    with conn:
        c = conn.cursor()
        c.execute("UPDATE authors SET wanna_contribute = (?) WHERE author_pk = (?)", (contribute_response ,author_pk))


def store_response(conn, data_dict, responses, agree_responses):
    assert len(responses) == len(data_dict['data'])
    assert len(agree_responses) == len(data_dict['data'])
    with conn:
        c = conn.cursor()

        c.execute("SELECT next_page_start from authors WHERE author_pk = (?)", (data_dict["author_pk"],))
        updated_pages_submitted = (int(c.fetchone()[0]) + 2)%5
        c.execute("UPDATE authors SET next_page_start = (?) WHERE author_pk = (?)", (updated_pages_submitted ,data_dict["author_pk"]))

        for i, data in enumerate(data_dict['data']):
            c.execute("UPDATE model_author_paper_similarity SET author_hand_confidence = (?), rating_agreement = (?) WHERE model_author_paper_pk = (?)", (responses[i], agree_responses[i], data[0]))
            conn.commit()
