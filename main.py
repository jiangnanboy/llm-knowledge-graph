# -*- coding: utf-8 -*-

import json
import os
import sys

from src.knowledge_graph.visualization import visual_graph

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add the parent directory to the Python path for imports
from src.img2txt.img_process import ocr_img
from src.pdf2img.pdf_process import pdf_img

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge_graph.config import load_config
from src.knowledge_graph.llm import call_llm, extract_json_from_text
from src.knowledge_graph.text_utils import chunk_text
from src.knowledge_graph.entity_standardization import standardize_entities, infer_relationships, limit_predicate_length
from src.knowledge_graph.prompts import MAIN_SYSTEM_PROMPT, MAIN_USER_PROMPT

def process_with_llm(config, input_text, debug=False):
    """
    Process input text with LLM to extract triples.
    
    Args:
        config: Configuration dictionary
        input_text: Text to analyze
        debug: If True, print detailed debug information
        
    Returns:
        List of extracted triples or None if processing failed
    """
    # Use prompts from the prompts module
    system_prompt = MAIN_SYSTEM_PROMPT
    user_prompt = MAIN_USER_PROMPT
    user_prompt += f"```\n{input_text}```\n" 

    # LLM configuration
    model = config["llm"]["model"]
    api_key = config["llm"]["api_key"]
    max_tokens = config["llm"]["max_tokens"]
    temperature = config["llm"]["temperature"]
    base_url = config["llm"]["base_url"]
    
    # Process with LLM
    metadata = {}
    response = call_llm(model, user_prompt, api_key, system_prompt, max_tokens, temperature, base_url)
    
    # Print raw response only if debug mode is on
    if debug:
        print("Raw LLM response:")
        print(response)
        print("\n---\n")
    
    # Extract JSON from the response
    result = extract_json_from_text(response)
    
    if result:
        # Validate and filter triples to ensure they have all required fields
        valid_triples = []
        invalid_count = 0
        
        for item in result:
            if isinstance(item, dict) and "subject" in item and "predicate" in item and "object" in item:
                # Add metadata to valid items
                valid_triples.append(dict(item, **metadata))
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            print(f"Warning: Filtered out {invalid_count} invalid triples missing required fields")
        
        if not valid_triples:
            print("Error: No valid triples found in LLM response")
            return None
        
        # Apply predicate length limit to all valid triples
        for triple in valid_triples:
            triple["predicate"] = limit_predicate_length(triple["predicate"])
        
        # Print extracted JSON only if debug mode is on
        if debug:
            print("Extracted JSON:")
            print(json.dumps(valid_triples, indent=2))  # Pretty print the JSON
        
        return valid_triples
    else:
        # Always print error messages even if debug is off
        print("\n\nERROR ### Could not extract valid JSON from response: ", response, "\n\n")
        return None

def process_text_in_chunks(config, full_text, debug=False):
    """
    Process a large text by breaking it into chunks with overlap,
    and then processing each chunk separately.
    
    Args:
        config: Configuration dictionary
        full_text: The complete text to process
        debug: If True, print detailed debug information
    
    Returns:
        List of all extracted triples from all chunks
    """
    # Get chunking parameters from config
    chunk_size = config.get("chunking", {}).get("chunk_size", 500)
    overlap = config.get("chunking", {}).get("overlap", 50)
    
    # Split text into chunks
    text_chunks = chunk_text(full_text, chunk_size, overlap)
    
    print("=" * 50)
    print("1: 三元组抽取")
    print("=" * 50)
    print(f"Processing text in {len(text_chunks)} chunks (size: {chunk_size} words, overlap: {overlap} words)")
    
    # Process each chunk
    all_results = []
    for i, chunk in enumerate(text_chunks):
        print(f"Processing chunk {i+1}/{len(text_chunks)} ({len(chunk.split())} words)")
        
        # Process the chunk with LLM
        chunk_results = process_with_llm(config, chunk, debug)
        
        if chunk_results:
            # Add chunk information to each triple
            for item in chunk_results:
                item["chunk"] = i + 1
            
            # Add to overall results
            all_results.extend(chunk_results)
        else:
            print(f"Warning: Failed to extract triples from chunk {i+1}")
    
    print(f"\nExtracted a total of {len(all_results)} triples from all chunks")
    
    # Apply entity standardization if enabled
    if config.get("standardization", {}).get("enabled", False):
        print("\n" + "="*50)
        print("2: 实体标准化")
        print("="*50)
        print(f"Starting with {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")
        
        all_results = standardize_entities(all_results, config)
        
        print(f"After standardization: {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")
    
    # Apply relationship inference if enabled
    if config.get("inference", {}).get("enabled", False):
        print("\n" + "="*50)
        print("3: 关系推理")
        print("="*50)
        print(f"Starting with {len(all_results)} triples")
        
        # Count existing relationships
        relationship_counts = {}
        for triple in all_results:
            relationship_counts[triple["predicate"]] = relationship_counts.get(triple["predicate"], 0) + 1
        
        print("Top 5 relationship types before inference:")
        for pred, count in sorted(relationship_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")
        
        all_results = infer_relationships(all_results, config)
        
        # Count relationships after inference
        relationship_counts_after = {}
        for triple in all_results:
            relationship_counts_after[triple["predicate"]] = relationship_counts_after.get(triple["predicate"], 0) + 1
        
        print("\nTop 5 relationship types after inference:")
        for pred, count in sorted(relationship_counts_after.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")
        
        # Count inferred relationships
        inferred_count = sum(1 for triple in all_results if triple.get("inferred", False))
        print(f"\nAdded {inferred_count} inferred relationships")
        print(f"Final knowledge graph: {len(all_results)} triples")
    
    return all_results

def get_unique_entities(triples):
    """
    Get the set of unique entities from the triples.
    
    Args:
        triples: List of triple dictionaries
        
    Returns:
        Set of unique entity names
    """
    entities = set()
    for triple in triples:
        if not isinstance(triple, dict):
            continue
        if "subject" in triple:
            entities.add(triple["subject"])
        if "object" in triple:
            entities.add(triple["object"])
    return entities

def main():
    # 加载配置
    config_file = 'config.toml'
    config = load_config(config_file)
    print('config:{}'.format(config))
    # 可以输入txt，image与pdf文件
    input_file ='/data/ai.txt'
    # 结果保存到html与json文件中
    html_output_file = '/data/knowledge_graph.html'
    json_output_file = '/data/knowledge_graph.json'

    file_format = input_file.split(".")[-1]
    file_format = file_format.lower()

    if file_format == 'txt':
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()
    elif file_format in ['png', 'jpg', 'jpeg', 'bmp']:
        input_text = ocr_img(input_file)
    elif file_format == 'pdf':
        pdf_imgs = pdf_img(input_file)
        input_text = ''
        for img in pdf_imgs:
            input_text += ocr_img(img)

    # 对读取的内容分块
    result = process_text_in_chunks(config, input_text, False)
    print(result)
    if result:
        # 保存原始数据为json格式
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # 可神化图谱html
        visual_graph(json_output_file, html_output_file)
        print("\n可视化html保存在以下路径中:")
        print(f"{html_output_file}")
    else:
        print("LLM处理出错，图谱生成失败！")

if __name__ == "__main__":
    main()
