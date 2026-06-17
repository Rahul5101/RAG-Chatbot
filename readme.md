#  Enterprise RAG Chatbot with Milvus, Redis, Persistent Memory & Multilingual Support

## Overview

This project is a production-oriented Retrieval-Augmented Generation (RAG) system designed to answer user queries using custom document knowledge bases while maintaining conversation context, reducing retrieval latency, and providing source-grounded responses.

Unlike traditional chatbot implementations that rely solely on Large Language Models (LLMs), this system augments generation with external knowledge retrieved from a vector database, enabling more accurate, up-to-date, and explainable responses.

The architecture combines:

* FastAPI Backend
* Milvus Vector Database
* Redis Cache Layer
* Persistent Conversation Memory
* Google Discovery Engine Integration
* PDF Knowledge Base Processing
* Multilingual Query Support
* Docker-Based Deployment

The system is designed to simulate the architecture used in modern enterprise AI assistants and knowledge management platforms.

---

#  Key Features

###  Retrieval-Augmented Generation (RAG)

* Semantic search over PDF documents
* Context-aware retrieval
* Source-grounded answer generation
* Hallucination reduction through retrieved context

###  Milvus Vector Database

* Stores document embeddings
* Performs high-speed vector similarity search
* Scalable retrieval architecture
* Optimized for large document collections

###  Redis Caching Layer

* Cache frequently asked questions
* Reduce retrieval latency
* Minimize repeated vector searches
* Improve response throughput

###  Persistent Memory

* Stores historical conversation context
* Enables multi-turn interactions
* Improves conversational continuity
* Allows long-running user sessions

###  Multilingual Support

* Query in multiple languages
* Language-independent semantic retrieval
* Cross-language document understanding

###  PDF Knowledge Base Processing

* Automated PDF ingestion
* Text extraction
* Chunk generation
* Embedding generation
* Vector indexing

###  Source Attribution

* Returns source documents
* Generates source URLs
* Improves answer explainability
* Enables fact verification

###  Google Discovery Engine Integration

* External document discovery
* Knowledge augmentation
* Enhanced information retrieval

###  Docker Deployment

* Containerized architecture
* Simplified deployment
* Environment consistency
* Scalable infrastructure

---

#  System Architecture

```text
                    ┌──────────────────┐
                    │     User Query   │
                    └────────┬─────────┘
                             │
                             ▼

                  ┌─────────────────────┐
                  │    FastAPI Server   │
                  └─────────┬───────────┘
                            │

          ┌─────────────────┼─────────────────┐
          │                 │                 │

          ▼                 ▼                 ▼

   Redis Cache      Persistent Memory    Query Processing
                                            │
                                            │
                                  |──┬────────────────┬────|
                                            │

                                            ▼

                                Embedding Generation

                                            │

                                            ▼

                                Milvus Vector Store

                                            │

                                            ▼

                                Top-K Document Retrieval

                                            │

                                            ▼

                                Context Construction

                                            │

                                            ▼

                                    LLM Generation

                                            │

                                            ▼

                                    Source Attribution

                                            │

                                            ▼

                                    Final Answer
```

---

#  End-to-End Workflow

## Step 1: Document Ingestion

PDF documents are uploaded into the system.

The ingestion pipeline:

```text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Embedding Generation
 ↓
Milvus Storage
```

Each chunk is converted into a dense vector representation and stored in Milvus.

---

## Step 2: User Query

The user submits a question.

Example:

```text
What are the advantages of transformer architectures?
```

---

## Step 3: Query Embedding

The query is converted into an embedding vector.

```text
User Query
 ↓
Embedding Model
 ↓
Vector Representation
```

---

## Step 4: Semantic Retrieval

Milvus performs nearest-neighbor search.

```text
Query Vector
 ↓
Milvus Search
 ↓
Top-K Relevant Chunks
```

The most relevant document chunks are returned.

---

## Step 5: Context Construction

Retrieved chunks are merged into a structured prompt.

```text
Retrieved Chunks
 +
Conversation History
 +
System Instructions
 ↓
Final Context
```

---

## Step 6: Response Generation

The LLM receives:

* User Query
* Retrieved Context
* Chat History

and generates a grounded answer.

---

## Step 7: Source Attribution

The system attaches:

* PDF source
* Page references
* URL references

to improve transparency.

---

#  Persistent Memory Design

Traditional RAG systems forget previous interactions.

This project introduces persistent memory that stores:

* User conversations
* Historical context
* Session information

Benefits:

* Better follow-up questions
* Context-aware responses
* Long-term conversations

Example:

```text
User:
Explain transformers.

User:
How does self-attention work?

The system remembers that
"self-attention" refers to transformers.
```

---

#  Redis Caching Strategy

Redis acts as a high-speed memory layer.

Cache Flow:

```text
User Query
 ↓
Redis Lookup

Cache Hit?
 ├── Yes → Return Response
 └── No
       ↓
     RAG Pipeline
       ↓
   Store in Redis
```

Benefits:

* Faster responses
* Reduced vector searches
* Lower inference cost

---

#  Milvus Vector Store

Milvus is used as the primary retrieval engine.

Responsibilities:

* Store embeddings
* Similarity search
* Metadata filtering
* Scalable retrieval

Why Milvus?

* High performance
* Enterprise-ready
* Horizontal scalability
* Optimized ANN search

---

#  Multilingual Retrieval

The system supports multilingual interactions.

Example:

```text
English Query
Hindi Query
<!-- French Query
Spanish Query -->
```

All queries are transformed into embeddings and searched against the same knowledge base.

---

<!-- #  Source URL Generator

Every generated answer can be traced back to its origin.

Features:

* Document references
* URL generation
* Source validation
* Explainable AI outputs -->

---

#  Tech Stack

| Component        | Technology              |
| ---------------- | ----------------------- |
| Backend          | FastAPI                 |
| Vector Database  | Milvus                  |
| Cache            | Redis                   |
| Embeddings       | Sentence Transformers   |
| LLM              | Configurable            |
| Containerization | Docker                  |
<!-- | Search Layer     | Google Discovery Engine | -->
| Language Support | Multilingual Embeddings |


---

# 🚀 Future Improvements

* Hybrid Search (BM25 + Dense Retrieval)
* Agentic RAG
* Graph RAG
* Multi-modal RAG
* Streaming Responses
* Distributed Milvus Clusters
* Advanced Memory Compression

---


---

# Author

Rahul Gupta

Machine Learning Engineer | AI Systems Enthusiast

Focused on:

* LLM Systems
* RAG Architectures
* AI Infrastructure
* Inference Optimization
* Production AI Systems
