from langchain.schema import HumanMessage, SystemMessage
import numpy
import spacy

nlp = spacy.load("en_core_web_sm")

def read_file(path):
    with open(path, 'r') as file:
        text = file.read().strip()

    return text

def prepare_msg(msg):    
    messages = [
        SystemMessage(
            content="Extract entities with their types (expected format: Entities: 1. entity (entity_type)) and \
                    relationships (expected format: Relationships:entity-[relationship]->entity) from given text in a list format. \
                    Restrictions: 1- Every entity in the relationships must be represented in entities. 2- Do not create dublicate entities. \
                    3- Entity and relationship names should be a single word. 4- Put '_' between two words if the relation name is more than one word. \
                    5- Assign order id for each line.\
                    6- Give descriptive entity types for each entity.\
                    7- Every strings in the response must comply to the Cypher query rules. No whitespaces."
        ),
        HumanMessage(content=msg)
    ]    

    return messages

def generate_batch(text):
    sentences = text.split(".")
    all_messages = []
    for sentence_id in range(0, len(sentences)-1, 2):
        batch = sentences[sentence_id:sentence_id+2]
        batch = '.'.join(batch)

        messages = prepare_msg(batch)        
        all_messages.append(messages)

    return all_messages

def get_unkown_word_type(word):
    doc = nlp(word)
    for token in doc:
        if len(token.ent_type_) > 0:
            return token.ent_type_.replace(" ", "_")
         
    return "Obj" # defult type

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
        r = r.split("-") # source - relation -> target
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