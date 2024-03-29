import time

import gradio as gr

from conf.config import Config
from neo4j_utils import *
from utils import *

conf = Config()
graph, chain = init_graph(
    openai_key=conf.openApi_key,
    graph_ip=conf.graph_ip,
    graph_port=conf.graph_port,
    graph_pass=conf.graph_password,
    graph_user=conf.graph_username
)
chat = ChatOpenAI(openai_api_key=conf.openApi_key)
file = None


def build_graphdb(msg4llm):
    message = chat(msg4llm)

    return message


def bot_response(message, history):
    global file

    if "generate from file:" in message:
        queries_str = ""
        unique_entity_type_list, unique_relation_list = [], []
        entity_list, type_list, relationship_list, entity_type_list = [], [], [], []

        path = f"../examples/{message.split(':')[1].strip()}"
        file = read_file("../examples/turkish_history.txt")
        print("FILE TEXT:", file)

        if file == "not_supported":
            return "Given file format is not supported by the chatbot"

        yield "Graph is building..."

        llmmsg = prepare_msg(file)
        objects = build_graphdb(msg4llm=llmmsg)

        entity_list, type_list, relationship_list, entity_type_list = parse_llm_response(objects)

        print("\nRelations:", relationship_list)
        print("\nEntities:", entity_type_list)

        yield "Given file is loaded"
        time.sleep(2)
        yield f"Entities:{entity_type_list}\nRelationships{relationship_list}"

        for id, entity_type in enumerate(entity_type_list):
            entity = entity_type[0]
            type = entity_type[1]

            entity_type_list[id] = (entity.strip().replace(" ", "_"), type.strip().replace(" ", "_"))

        for id, relation in enumerate(relationship_list):
            source = relation[0]
            relationship = relation[1]
            target = relation[2]

            relationship_list[id] = [source.strip().replace(" ", "_"), relationship.strip().replace(" ", "_"),
                                     target.strip().replace(" ", "_")]

        time.sleep(2)
        generated_queries = cypher_query(relationship_list, entity_type_list)
        for q in generated_queries:
            queries_str = f"\n{q}"

        for q in generated_queries:
            execute_query(q, graph)
        queries_str += "\nDone"

        yield queries_str

    elif "run query:" in message:
        q = message.split("run query:")[1].strip()
        resp = execute_query(q, graph)

        yield "Done"
    else:
        if file is None and len(graph_schema(graph=graph)) == 117:
            yield "First, load a file. Database is empty."
        else:
            print("Waiting for model response...")
            time.sleep(2)
            resp = search_on_graph(message, chain, graph)

            yield resp


gr.ChatInterface(bot_response).launch()
