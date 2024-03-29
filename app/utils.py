import spacy
from langchain.schema import HumanMessage, SystemMessage
from pypdf import PdfReader

nlp = spacy.load("en_core_web_sm")


def read_file(path):
    path_extention = path.split(".")[-1]

    if path_extention == "txt":
        with open(path, 'r') as file:
            text = file.read().strip()
    elif path_extention == "pdf":
        reader = PdfReader(path)
        num_of_pages = len(reader.pages)
        text = ""
        for page_num in range(num_of_pages):
            page = reader.pages[page_num]
            text += str(page.extract_text())
    else:
        text = "not_supported"
    return text


def prepare_msg(msg):
    messages = [
        SystemMessage(
            content=
            """
            Extract entities with their types (expected format: Entities: 1. entity (entity_type)) and \
            relationships (expected format: Relationships:entity-[relationship]->entity) from given text in \
            a list format. \
            Restrictions: \
            1- Every entity in the relationships must be represented in entities.  \
            2- Give descriptive entity types for each entity.\
            3- Do not create duplicate entities. \
            4- Entity labels and relationship labels should be single words. \
            5- Put '_' between two words only if the relationship or entity label is more than one word. \
            6- Entity and relationship names labels should NOT contain punctuation or special characters. \
            7- Entity and relationship labels should NOT contain punctuation or special characters. \
            8- Assign order id for each line.\
            9- Every entity label and relationship label in the response must comply to the Cypher query rules.\
             No whitespaces, no Apostrophes.\
            """
        ),
        HumanMessage(content=msg)
    ]

    return messages


def generate_batch(text):
    sentences = text.split(".")
    all_messages = []
    for sentence_id in range(0, len(sentences) - 1, 2):
        batch = sentences[sentence_id:sentence_id + 2]
        batch = '.'.join(batch)

        messages = prepare_msg(batch)
        all_messages.append(messages)

    return all_messages


def get_unkown_word_type(word):
    doc = nlp(word)
    for token in doc:
        if len(token.ent_type_) > 0:
            return token.ent_type_.replace(" ", "_")

    return "Obj"  # defult type


def parse_llm_response(model_response):
    resp = model_response.content
    rel_id = resp.find("Relationships")
    ents = resp[:rel_id]
    relationships = resp[rel_id:]

    entity_list = []
    type_list = []
    relationship_list = []

    for e in ents.split("\n")[1:]:
        e = e.split(".")
        if len(e) > 1:
            entity_with_type = ''.join(e[1:]).strip()

            entity = entity_with_type.split("(")[0].strip().replace(" ", "_")
            entity_type = entity_with_type.split("(")[1].replace(")", "")

            entity_list.append(entity)
            type_list.append(entity_type)

    for r in relationships.split("\n")[1:]:
        r = r.split(".")
        r = ''.join(r[1:]).strip()
        r = r.split("-")  # source - relation -> target
        if len(r) > 1:
            source = r[0].strip().replace(" ", "_")
            relation = r[1][1:-1].strip().replace(" ", "_")
            target = r[2][1:].strip().replace(" ", "_")

            if source not in entity_list:
                entity_type = get_unkown_word_type(source).strip().replace(" ", "_")
                entity_list.append(source)
                type_list.append(entity_type)

            if target not in entity_list:
                entity_type = get_unkown_word_type(source).strip().replace(" ", "_")
                entity_list.append(target)
                type_list.append(entity_type)

            relationship_list.append(
                [source, relation, target]
            )

    entity_type_list = list(zip(entity_list, type_list))

    return entity_list, type_list, relationship_list, entity_type_list
