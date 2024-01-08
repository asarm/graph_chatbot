from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.graphs import Neo4jGraph

from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.llms import GPT4All
from langchain_community.vectorstores import Chroma
from langchain.chains import GraphCypherQAChain
from langchain_community.chat_models import ChatOpenAI

def init_graph(OPENAIKEY):
    graph = Neo4jGraph(
        url="bolt://localhost:7687", username="neo4j", password="chatbot123"
    )
    chain = GraphCypherQAChain.from_llm(
        ChatOpenAI(temperature=0, openai_api_key=OPENAIKEY), graph=graph, verbose=False
    )

    return graph, chain

def graph_schema(graph:Neo4jGraph):
    graph.refresh_schema()

    return graph.schema

def execute_query(q, graph:Neo4jGraph):
    resp = graph.query(
        q
    )    
    graph.refresh_schema()

    return resp

def search_on_graph(q, chain:GraphCypherQAChain, graph:Neo4jGraph):
    graph.refresh_schema()
    resp = chain.run(q)

    return resp

def search_entity_type(search_key, entity_type_list):
    for i in entity_type_list:
        if search_key == i[0]:
            return i[1]
        
    return "Node"

def cypher_query(relationship_list, entity_type_list, mode="CREATE"):
    queries = []
    for entity_id in range(len(entity_type_list)):
        query = ""
        obj = entity_type_list[entity_id]
        entity = obj[0]
        entity_type = obj[1] 

        query += "CREATE (:" + entity_type + " {name:'"+ entity +"'}" + ")"
        
        queries.append(query)

    for r_id, r in enumerate(relationship_list):
        query = ""
        source = r[0]
        source_type = search_entity_type(source, entity_type_list) 
        source_variable = source_type.lower() 

        relation = r[1]

        target = r[2] 
        target_type = search_entity_type(target, entity_type_list)
        target_variable = target_type.lower() if target_type.lower() != source_variable else target_type.lower()+"_2"

        # print(source, entity_type_list[r_id])
        query += f"MATCH ({source_variable}: {source_type} {{name:'{source}'}})"
        query += f" MATCH ({target_variable}: {target_type} {{name:'{target}'}})" 
        query += f" {mode} ({source_variable})-[:{relation.lower()}]->({target_variable})"

        queries.append(query)
        
    return queries