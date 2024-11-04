# cllm - [C]ommand-line [LLM] usage

## Quickstart

To get started with cllm:

1. Clone the repository:
   ```
   git clone https://github.com/m9e/cllm.git
   cd cllm
   ```

2. Run the installation script:
   ```
   sudo ./install_cllm.sh
   ```

3. Set up your Azure OpenAI credentials:
   ```
   export AZURE_OPENAI_API_KEY=your_api_key_here
   export AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
   ```

4. You can now use the `cllm` command from anywhere on your system.

## GPT o1 notes

For the `o1` openai models:

- no system prompt is allowed
- we assume o1 if model name contains "o1" anywhere
- we swap max_tokens -> max_completion_tokens; param is the same
- update `openai` package (`pip install -U openai`) if you get an error about `max_completion_tokens`

## Usage

See [examples in Notebook form](sample_usage.ipynb)

```
mikoshi:cllm matt$ cllm -h
usage: cllm [-h] [-d DIRECTORY] [-p PROMPT] [-c CONTEXT_LENGTH] [-s SUMMARY] [-m MODEL] [--system SYSTEM] [-f FILTER] [--stats] [-v] [-e EXTENSIONS]
            [-l LIMIT] [-B BASE_URL] [--expand-prompt EXPAND_PROMPT] [-x] [-S] [-o OVERLAP] [-b] [--send-empty] [--tc] [-n MAX_INFERENCE_CALLS]
            [-I [INPUT ...]]
            ...

Composable command-line interactions with LLM APIs

positional arguments:
  inline_prompt         Unmatched arguments to be used as the prompt if -p is not provided

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        Directory to process
  -p PROMPT, --prompt PROMPT
                        User prompt
  -c CONTEXT_LENGTH, --context-length CONTEXT_LENGTH
                        Context length for splitting files/input
  -s SUMMARY, --summary SUMMARY
                        Summary prompt
  -m MODEL, --model MODEL
                        Model name
  --system SYSTEM       System message
  -f FILTER, --filter FILTER
                        Filter files by string in path
  --stats               Print statistics
  -v, --verbose         Print raw request, response, params to stderr
  -e EXTENSIONS, --extensions EXTENSIONS
                        Comma-separated list of file extensions to process
  -l LIMIT, --limit LIMIT
                        Limit output tokens
  -B BASE_URL, --base-url BASE_URL
                        (Optional) Base URL for OpenAI-compatible API, defaults to the standard OpenAI API endpoint
  --expand-prompt EXPAND_PROMPT
                        Prompt for prompt expansion, passed without the input to let the LLM craft a better prompt
  -x                    Expand the user prompt by pre-processing it with an LLM to try optimizing the result
  -S, --single-string-stdin
                        Treat all stdin as a single string instead of prompting with each line
  -o OVERLAP, --overlap OVERLAP
                        Number of bytes to include before the split if the chunk is larger than the context
  -b, --progress-bar    Display a progress bar based on the total bytes of the files processed
  --send-empty          Send empty lines with as empty context with the prompt instead of just emitting them back to stdout; no effect if -S is set
  --tc                  Token count mode: count tokens instead of processing prompts
  -n MAX_INFERENCE_CALLS, --max-inference-calls MAX_INFERENCE_CALLS
                        Maximum number of API calls to make
  -I [INPUT ...], --input [INPUT ...]
                        Input argument; usually read from stdin or provided as additional arguments
```

## Roadmap/TODO

- [] Test/fix the extend-prompt/summarizer functions
- [] Fix progress bar stuff

## Immediate Improvement ideas

- [] Leverage non-OpenAI APIs
- [] File-In-File-Out (eg, input.txt -> input.txt.llm, input2.txt -> input2.txt.llm or something)
- [] Add some examples and add DSPy to "compile" prompts for flexibility?
- [] Allow user to pass more params to endpoint (eg, temperature)
- [] Allow user to specify certain params like BASE_URL via env vars (eg `CLLM_BASE_URL`)
