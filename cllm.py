#!/usr/bin/env python

# cllm: (c)ommand-line (llm) access

# For examples see https://github.com/m9e/cllm notebook

# (c) Copyright Matthew Wallace 2024; Licensed under Apache-2.0 Text version: https://www.apache.org/licenses/LICENSE-2.0.txt (see LICENSE)

import os
import sys
import select
import argparse
import openai
import tiktoken
from gitignore_parser import parse_gitignore
import time
import json
from tqdm import tqdm
from typing import List, Optional, Generator, Tuple
import pyperclip

DEFAULT_SYSTEM = (
    "You are an AI used to do thing in a command line pipeline. "
    "You are given a prompt which may include context. If there is context, "
    "you must do your best with the context but you must NOT explain or discuss your output. "
    "e.g., if your task was Translate to Spanish | Context: I like to eat frogs\n\n"
    "If there were two translations you must not discuss the options, you must simply select the best and output it. "
    "Think of yourself as an advanced version of sed, awk, grep, etc, and as such, you transform the context with the prompt as best you can but you never output anything not asked for."
    "As a rule if you are outputting code, as this is CLI, that means you must avoid ```bash``` type enclosures unless specifically asked for or they were part of the context."
)

def read_file_in_chunks(file_path: str, chunk_size: int) -> Generator[str, None, None]:
    """Read a file in chunks of specified size.
    
    Args:
        file_path (str): The path to the file to read.
        chunk_size (int): The number of lines to read per chunk.
    
    Yields:
        Generator[str, None, None]: A generator yielding chunks of the file as strings.
    """
    with open(file_path, 'r') as file:
        while True:
            lines = []
            for _ in range(chunk_size):
                line = file.readline()
                if not line:
                    break
                lines.append(line)
            if not lines:
                break
            yield ''.join(lines).strip()

def resolve_and_normalize_path(path: str) -> str:
    """Resolve and normalize the given path.
    
    Args:
        path (str): The path to resolve and normalize.
    
    Returns:
        str: The resolved and normalized path.
    """
    return os.path.realpath(os.path.abspath(path))

def load_gitignore_files(directory: str) -> dict:
    """Load .gitignore files from the directory and its parents, mapping them to their directories.
    
    Args:
        directory (str): The directory to start loading .gitignore files from.
    
    Returns:
        dict: A dictionary mapping directories to their .gitignore matchers.
    """
    gitignore_map = {}
    normalized_directory = resolve_and_normalize_path(directory)
    
    current_dir = normalized_directory
    while current_dir != os.path.dirname(current_dir):  # Stop at the root directory
        gitignore_path = os.path.join(current_dir, '.gitignore')
        if os.path.exists(gitignore_path):
            gitignore_map[current_dir] = parse_gitignore(gitignore_path)
        current_dir = os.path.dirname(current_dir)

    # Check the current working directory's .gitignore
    cwd_gitignore_path = resolve_and_normalize_path(os.path.join(os.getcwd(), '.gitignore'))
    if os.path.exists(cwd_gitignore_path) and cwd_gitignore_path.startswith(normalized_directory):
        gitignore_map[os.getcwd()] = parse_gitignore(cwd_gitignore_path)

    return gitignore_map

def is_file_ignored_by_gitignore(file_path: str, gitignore_map: dict) -> bool:
    """Check if a file is ignored by any .gitignore matcher based on its directory.
    
    Args:
        file_path (str): The path to the file to check.
        gitignore_map (dict): A dictionary mapping directories to their .gitignore matchers.
    
    Returns:
        bool: True if the file is ignored, False otherwise.
    """
    normalized_file_path = resolve_and_normalize_path(file_path)
    for directory, matcher in gitignore_map.items():
        try:
            if matcher(normalized_file_path):
                return True
        except ValueError as e:
            print(f"Error checking file '{normalized_file_path}' against .gitignore in '{directory}': {e}", file=sys.stderr)
    return False

def call_openai_api(client, model: str, prompt: str, system_message: Optional[str] = None, limit: Optional[int] = None, temperature: Optional[float] = None, verbose: bool = False) -> Tuple[str, float]:
    """Call the OpenAI API with the given parameters.
    
    Args:
        client: The OpenAI client.
        model (str): The model to use for the API call.
        prompt (str): The user prompt.
        system_message (Optional[str]): The system message to use.
        limit (Optional[int]): The maximum number of tokens to generate.
        temperature (Optional[float]): The sampling temperature to use.
        verbose (bool): Whether to print verbose output.
    
    Returns:
        Tuple[str, float]: The response content and the elapsed time for the API call.
    """
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    else:
        messages.append({"role": "system", "content": DEFAULT_SYSTEM})
    messages.append({"role": "user", "content": prompt})
    if verbose:
        print(f"Raw request:\nModel: {model}\nMessages: {json.dumps(messages, indent=2)}\n", file=sys.stderr)
        print(f"Parameters:\nLimit: {limit}\nTemperature: {temperature}\n", file=sys.stderr)

    start_time = time.time()
    
    # Call the API with conditional parameters
    if limit is not None and temperature is not None:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=limit,
            temperature=temperature
        )
    elif limit is not None:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=limit
        )
    elif temperature is not None:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
    
    elapsed_time = time.time() - start_time

    if verbose:
        print(f"Raw response:\n\t{str(response)}\n----------------\n\n", file=sys.stderr)

    return response.choices[0].message.content, elapsed_time

def count_tokens(text: str, encoder) -> int:
    """Count the number of tokens in the given text using the specified encoder.
    
    Args:
        text (str): The text to count tokens in.
        encoder: The encoder to use for counting tokens.
    
    Returns:
        int: The number of tokens in the text.
    """
    return len(encoder.encode(text))

def get_files_and_sizes(directory: str, extensions: Optional[List[str]], file_filter: Optional[str], gitignore_map: dict) -> List[Tuple[str, int]]:
    """Get a list of files and their sizes in the directory.
    
    Args:
        directory (str): The directory to search for files.
        extensions (Optional[List[str]]): A list of file extensions to include.
        file_filter (Optional[str]): A string to filter files by.
        gitignore_map (dict): A dictionary mapping directories to their .gitignore matchers.
    
    Returns:
        List[Tuple[str, int]]: A list of tuples containing file paths and their sizes.
    """
    files_and_sizes = []
    visited_inodes = set()  # To keep track of visited inodes to prevent infinite loops

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                if file_filter and file_filter not in os.path.join(root, file):
                    continue
                file_path = os.path.join(root, file)
                if not is_file_ignored_by_gitignore(file_path, gitignore_map):
                    try:
                        inode = os.stat(file_path).st_ino
                        if inode in visited_inodes:
                            continue  # Skip files that have already been visited
                        visited_inodes.add(inode)
                        files_and_sizes.append((file_path, os.path.getsize(file_path)))
                    except OSError as e:
                        print(f"Error accessing file {file_path}: {e}", file=sys.stderr)
                        continue  # Skip files that cause an OSError

    return files_and_sizes

def process_files(directory: str, context_length: int, extensions: Optional[List[str]], file_filter: Optional[str], verbose: bool, token_count_mode: bool, encoder, gitignore_map: dict) -> Generator[Tuple[str, str, str], None, None]:
    """Process files in the directory with the given parameters and yield chunks.
    
    Args:
        directory (str): The directory to process files in.
        context_length (int): The context length for splitting files/input.
        extensions (Optional[List[str]]): A list of file extensions to include.
        file_filter (Optional[str]): A string to filter files by.
        verbose (bool): Whether to print verbose output.
        token_count_mode (bool): Whether to count tokens instead of processing prompts.
        encoder: The encoder to use for counting tokens.
        gitignore_map (dict): A dictionary mapping directories to their .gitignore matchers.
    
    Yields:
        Generator[Tuple[str, str, str], None, None]: A generator yielding tuples of file path, start line, and chunk.
    """
    files_and_sizes = get_files_and_sizes(directory, extensions, file_filter, gitignore_map)

    for file_path, file_size in tqdm(files_and_sizes, desc="Processing files", unit="B", unit_scale=True, disable=not verbose):
        start_line = 1
        chunk = ""
        for line in read_file_in_chunks(file_path, 100):  # Read in chunks of 100 lines
            chunk += line + "\n"
            token_count = count_tokens(chunk, encoder)
            if verbose:
                print(f"Processing {file_path}, start_line {start_line}, token_count {token_count}", file=sys.stderr)
            if token_count > context_length:
                split_point = chunk[:context_length].rfind(' ')
                if split_point == -1:
                    split_point = context_length
                chunk_to_send = chunk[:split_point]
                remaining = chunk[split_point:].strip()
                yield file_path, start_line, chunk_to_send
                start_line += chunk_to_send.count('\n')
                chunk = remaining
        if chunk:
            yield file_path, start_line, chunk
def main():
    """Main function to parse arguments and process files or stdin."""
    parser = argparse.ArgumentParser(description="Composable command-line interactions with LLM APIs")
    parser.add_argument('-d', '--directory', help='Directory to process')
    parser.add_argument('-p', '--prompt', help='User prompt')
    parser.add_argument('-c', '--context-length', type=int, default=4096, help='Context length for splitting files/input (default: 4096)')
    parser.add_argument('-s', '--summary', help='Summary prompt')
    parser.add_argument('-m', '--model', help='Model name; or deployment for Azure OpenAI (default: gpt-4o-2024-08-06 or "model" if -B is set)')
    parser.add_argument('--system', help='System message')
    parser.add_argument('-f', '--filter', help='Filter files by string in path')
    parser.add_argument('--stats', action='store_true', help='Print statistics')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print raw request, response, params to stderr')
    parser.add_argument('-vv', '--very-verbose', action='store_true', help='Enable verbose and very verbose mode')
    parser.add_argument('-e', '--extensions', help='Comma-separated list of file extensions to process')
    parser.add_argument('-l', '--limit', type=int, default=1024, help='Limit output tokens (default: 1024)')
    parser.add_argument('-B', '--base-url', help='(Optional) Base URL for OpenAI-compatible API, defaults to the standard OpenAI API endpoint')
    parser.add_argument('--expand-prompt', help='Prompt for prompt expansion, passed without the input to let the LLM craft a better prompt')
    parser.add_argument('-x', action='store_true', help='Expand the user prompt by pre-processing it with an LLM to try optimizing the result')
    parser.add_argument('-S', '--single-string-stdin', action='store_true', default=False, help='Treat all stdin as a single string instead of prompting with each line (default: False)')
    parser.add_argument('-o', '--overlap', type=int, help='Number of bytes to include before the split if the chunk is larger than the context')
    parser.add_argument('-b', '--progress-bar', action='store_true', help='Display a progress bar based on the total bytes of the files processed')
    parser.add_argument('--send-empty', action='store_true', help='Send empty lines with as empty context with the prompt instead of just emitting them back to stdout; no effect if -S is set')
    parser.add_argument('--tc', action='store_true', help='Token count mode: count tokens instead of processing prompts')
    parser.add_argument('-n', '--max-inference-calls', type=int, default=None, help='Maximum number of API calls to make (default: None)')
    parser.add_argument('-I', '--input', nargs='*', default=[], help='Input argument; usually read from stdin or provided as additional arguments (default: [])')
    parser.add_argument('-M', '--mode', choices=['default', 'azure'], default='default', help='Mode to run the script in: "default" or "azure" (default: default)')
    parser.add_argument('-C', '--clipboard', action='store_true', help='Get the context from the clipboard')
    parser.add_argument('-t', '--temperature', type=float, help='Temperature for the model')
    parser.add_argument('inline_prompt', nargs=argparse.REMAINDER, help='Unmatched arguments to be used as the prompt if -p is not provided')
    args = parser.parse_args()

    # Set verbose and very_verbose flags
    if args.very_verbose:
        args.verbose = True
        very_verbose = True
    else:
        very_verbose = False

    if args.prompt and args.inline_prompt:
        print("Error: pass -p prompt or inline-prompt, not both", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if not args.prompt:
        args.prompt = ' '.join(args.inline_prompt)

    if not args.prompt:
        print("Error: no prompt provided", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if args.directory and not args.extensions:
        print("Error: If -d is passed, -e must be passed as well.", file=sys.stderr)
        sys.exit(1)
    
    if args.directory and not sys.stdin.isatty():
        print("Error: If -d is passed, stdin should not be used.", file=sys.stderr)
        sys.exit(1)
    
    if args.clipboard and not sys.stdin.isatty():
        print("Error: If -C is passed, stdin should not be used.", file=sys.stderr)
        sys.exit(1)

    if args.temperature is not None:
        try:
            args.temperature = float(args.temperature)
        except ValueError:
            print("Error: Temperature must be a number.", file=sys.stderr)
            sys.exit(1)

    if not args.base_url and os.getenv('CLLM_BASE_URL'):
        args.base_url = os.getenv('CLLM_BASE_URL')

    if not args.model:
        if args.base_url:
            args.model = 'model'
        else:
            args.model = 'gpt-4o-2024-08-06'

    extensions = args.extensions.split(',') if args.extensions else None

    # Determine API key and base URL
    if args.base_url and args.mode != 'azure' and not args.base_url.lower().endswith(('azure.com', 'microsoft.com')):
        # User specified a non-Azure base URL, use vanilla OpenAI mode
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key and not args.base_url.lower().endswith('openai.com'):
            api_key = 'NO_KEY_SUPPLIED'
        client = openai.OpenAI(
            api_key=api_key,
            base_url=args.base_url
        )
    elif args.mode == 'azure' or os.getenv('OPENAI_API_TYPE') == 'azure' or (not os.getenv('OPENAI_API_KEY') and os.getenv('AZURE_OPENAI_API_KEY')):
        # Load environment variables
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
            api_version="2023-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    else:
        base_url = os.getenv('OPENAI_API_BASE') or None
        api_key = os.getenv('OPENAI_API_KEY')

        if base_url:
            client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            client = openai.OpenAI(api_key=api_key)

    if args.expand_prompt:
        expand_prompt = args.expand_prompt or (
            "Act as an elite prompt engineer working on an important project. The user is about to call an LLM in a bash pipeline, "
            "using the LLM as a super-sophisticated sed/awk/etc, but with high-intelligence transformation. You must expand the simple "
            "prompt to a fully fleshed-out prompt. Your prompt MUST include instructions to the LLM to be mindful of this circumstance "
            "(bash pipeline) and instruct it to not output backticks or any such thing. You may see tokens in the prompt such as "
            "{{context}} or {{filename}}; your prompt should use those verbatim; after your prompt is returned, when we call the LLM with "
            "it, those strings will be substituted. Ensure the LLM understands it must avoid any extraneous output; no backticks, no "
            "extemporaneous discussion. If the request is unfulfillable and the LLM believes it cannot properly produce a reply, it should "
            "return the string 'False ({{failure_reason}})' where failure_reason is its reason; it should understand that will go to stderr "
            "and the original input will go to stdout to attempt to cause a minimal disruption. "
            "Tell the LLM to use newlines judiciously; we will neither add nor remove them; it should output them typically if a newline is "
            "part of the input, but if the user is instructing it to, say, concatenate multiple lines in a way then it may not want to "
            "put a newline in the output. "
            "Additionally, if the user prompt does not contain the slug '{{context}}' then there is nowhere for the user input to go; which "
            "means you must tell the model to ADD the '{{context}}' slug at the end, so that when we format the stdin input it is inserted. "
            "You must now craft the prompt with these requirements in mind. Both you and the LLM should take a deep breath, think step by step, "
            "output the most optimal output, being very mindful of the VERY STRICT requirements. If you and the LLM both are successful, you will "
            "save lives. If you fail, innocent people may suffer grievous harm, so it is critical for you to succeed, and for the LLM to succeed, and you should "
            "do your absolute best. Here is the prompt, with a single space after the colon and no other formatting: {prompt}"
        )
        expanded_prompt, _ = call_openai_api(client, args.model, expand_prompt.format(prompt=args.prompt), args.system, args.limit, args.temperature, args.verbose)
        args.prompt = expanded_prompt

    try:
        encoder = tiktoken.encoding_for_model(args.model)
    except Exception as e:
        print(f"Tokenizer for splits: could not load tokenizer for model {args.model} so using gpt-4; reducing context length by 5% to prevent overflows", file=sys.stderr)
        encoder = tiktoken.encoding_for_model('gpt-4')
        args.context_length = int(args.context_length * 0.95)

    total_api_time = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_api_calls = 0

    if args.verbose:
        print(f"directory is {args.directory}", file=sys.stderr)
        print(f"context_length is {args.context_length}", file=sys.stderr)
        print(f"file_filter is {args.filter}", file=sys.stderr)
        print(f"verbose is {args.verbose}", file=sys.stderr)
        print(f"extensions is {extensions}", file=sys.stderr)
        print(f"token_count_mode is {args.tc}", file=sys.stderr)
        print(f"model is {args.model}", file=sys.stderr)

    if args.directory:
        gitignore_map = load_gitignore_files(args.directory)
        for file_path, start_line, chunk in process_files(
            directory=args.directory,
            context_length=args.context_length,
            extensions=extensions,
            file_filter=args.filter,
            verbose=args.verbose,
            token_count_mode=args.tc,
            encoder=encoder,
            gitignore_map=gitignore_map
        ):
            if args.verbose:
                print(f"Input Processing: file_path: {file_path}, start_line: {start_line}, chunk: {chunk}", file=sys.stderr)
            if '{context}' not in args.prompt:
                args.prompt += ' | Context: {context}'
            prompt = args.prompt.format(filename=file_path, startline=start_line, context=chunk)
            response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
            total_api_time += elapsed_time
            total_input_tokens += count_tokens(prompt, encoder)
            total_output_tokens += count_tokens(response, encoder)
            total_api_calls += 1
            print(response)
            if args.max_inference_calls and total_api_calls >= args.max_inference_calls:
                break
    else:
        if args.clipboard:
            context = pyperclip.paste()
            if '{context}' not in args.prompt and context.strip():
                args.prompt += ' | Context: {context}'
            prompt = args.prompt.format(context=context.strip())
            response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
            total_api_time += elapsed_time
            total_input_tokens += count_tokens(prompt, encoder)
            total_output_tokens += count_tokens(response, encoder)
            total_api_calls += 1
            print(response)
        elif sys.stdin.isatty():
            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    stdin_content = sys.stdin.read()
                    if args.single_string_stdin:
                        if '{context}' not in args.prompt and stdin_content.strip():
                            args.prompt += ' | Context: {context}'
                        prompt = args.prompt.format(context=stdin_content.strip())
                        response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
                        total_api_time += elapsed_time
                        total_input_tokens += count_tokens(prompt, encoder)
                        total_output_tokens += count_tokens(response, encoder)
                        total_api_calls += 1
                        print(response)
                    else:
                        for line in stdin_content.splitlines():
                            if '{context}' not in args.prompt and line.strip():
                                args.prompt += ' | Context: {context}'
                            prompt = args.prompt.format(context=line.strip())
                            response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
                            total_api_time += elapsed_time
                            total_input_tokens += count_tokens(prompt, encoder)
                            total_output_tokens += count_tokens(response, encoder)
                            total_api_calls += 1
                            print(response)
                            if args.max_inference_calls and total_api_calls >= args.max_inference_calls:
                                break
                else:
                    context = ''
                    prompt = args.prompt.format(context=context)
                    response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
                    total_api_time += elapsed_time
                    total_input_tokens += count_tokens(prompt, encoder)
                    total_output_tokens += count_tokens(response, encoder)
                    total_api_calls += 1
                    print(response)
            except select.error:
                context = ''
                prompt = args.prompt.format(context=context)
                response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
                total_api_time += elapsed_time
                total_input_tokens += count_tokens(prompt, encoder)
                total_output_tokens += count_tokens(response, encoder)
                total_api_calls += 1
                print(response)
        else:
            # Blocking read from pipe
            stdin_content = sys.stdin.read()
            if args.single_string_stdin:
                if '{context}' not in args.prompt and stdin_content.strip():
                    args.prompt += ' | Context: {context}'
                context = stdin_content.strip()
                while context:
                    # Tokenize the context to ensure it doesn't exceed the context length
                    tokenized_context = encoder.encode(context)
                    if len(tokenized_context) > args.context_length:
                        split_point = args.context_length
                        while split_point > 0 and tokenized_context[split_point] != ' ':
                            split_point -= 1
                        if split_point == 0:
                            split_point = args.context_length
                        chunk_to_send = encoder.decode(tokenized_context[:split_point])
                        remaining = encoder.decode(tokenized_context[split_point:])
                    else:
                        chunk_to_send = context
                        remaining = ''
                    
                    prompt = args.prompt.format(context=chunk_to_send)
                    response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
                    total_api_time += elapsed_time
                    total_input_tokens += count_tokens(prompt, encoder)
                    total_output_tokens += count_tokens(response, encoder)
                    total_api_calls += 1
                    print(response)
                    context = remaining
                    if args.max_inference_calls and total_api_calls >= args.max_inference_calls:
                        break
            else:
                for line in stdin_content.splitlines():
                    if not args.send_empty and not line.strip():
                        print("")
                        continue
                    if '{context}' not in args.prompt and line.strip():
                        args.prompt += ' | Context: {context}'
                    prompt = args.prompt.format(context=line.strip())
                    response, elapsed_time = call_openai_api(client, args.model, prompt, args.system, args.limit, args.temperature, args.verbose)
                    total_api_time += elapsed_time
                    total_input_tokens += count_tokens(prompt, encoder)
                    total_output_tokens += count_tokens(response, encoder)
                    total_api_calls += 1
                    print(response)
                    if args.max_inference_calls and total_api_calls >= args.max_inference_calls:
                        break

    if args.stats:
        print("\n---- Stats ----", file=sys.stderr)
        print(f"Total execution time (API calls): {total_api_time:.2f} seconds", file=sys.stderr)
        print(f"Total input tokens: {total_input_tokens}", file=sys.stderr)
        print(f"Total output tokens: {total_output_tokens}", file=sys.stderr)
        print(f"Input tokens/sec: {total_input_tokens / total_api_time:.2f}", file=sys.stderr)
        print(f"Output tokens/sec: {total_output_tokens / total_api_time:.2f}", file=sys.stderr)
        print(f"Total API calls made: {total_api_calls}", file=sys.stderr)

if __name__ == "__main__":
    main()

