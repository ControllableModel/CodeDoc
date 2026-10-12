## ClassDef LinguisticCore
**LinguisticCore**: The function of LinguisticCore is to manage interactions with a language model, handle user data, and facilitate conversation history and context.

**attributes**: The attributes of this Class.
· user_personal_data: A boolean indicating whether to store user personal data.
· name: A string representing the name of the user.
· user: A string representing the username.
· client: An instance of the OpenAI client for API interactions.
· LLM_url: A string containing the URL for the language model service.
· LLM_key: A string holding the API key for authentication.
· model: A string specifying the model to be used for language processing.
· profile: A string containing the profile information for the user.
· setting: A string for configuration settings.
· example: A string providing example interactions.
· world: A string for contextual information about the conversation.
· world_dict: A dictionary mapping terms to their definitions or explanations.
· story: A dictionary to hold story-related data.
· history_list: A list to maintain the history of messages exchanged.
· round: An integer representing the number of messages to retain in history.
· result: A list to store results from interactions.
· input: A list to hold input messages.
· first: A string for initial message content.
· tools: A list of tools available for interaction.
· tool_choice: A string indicating the choice of tool usage.
· tool: An object representing the currently selected tool.
· msg: A message object for processing.
· add_msg: A string for additional messages.
· temperature: A float controlling the randomness of responses.
· access_list: A dictionary containing access-related information.
· web_search: A boolean indicating whether web search is enabled.
· call_robot: A boolean indicating whether to allow robot responses.
· db: An instance of MemoryDataCore for managing user data if user_personal_data is true.

**Code Description**: The LinguisticCore class is designed to facilitate interactions with a language model by managing user data, conversation history, and contextual information. Upon initialization, it sets up various attributes including user information, API credentials, and configurations for the language model. The create_socket method establishes a connection to the OpenAI API using the provided credentials. The world_add method enriches the conversation context by adding definitions from the world_dict and performing web searches if enabled. The func_call method processes function calls from messages. The introduce method provides a summary of available tools and their descriptions. The pr_agent and pr_chat methods prepare messages for interaction with the language model, incorporating conversation history and context. The add_data method stores conversation history in a database if user_personal_data is enabled. The process method orchestrates the interaction with the language model, handling different modes such as chat, agent, and tool usage, and manages the conversation flow based on the responses received.

**Note**: It is important to ensure that the LLM_key and LLM_url are correctly set for successful API interactions. Additionally, when user_personal_data is enabled, appropriate data management practices should be followed to protect user privacy.

**Output Example**: An example output from the process method when interacting in chat mode could be:
"Hello! How can I assist you today?
>>>
I'm looking for information on the latest advancements in AI."
### FunctionDef __init__(self, user_personal_data)
**__init__**: The function of __init__ is to initialize an instance of the class with default attributes and optional user personal data.

**parameters**: The parameters of this Function.
· user_personal_data: A boolean value that indicates whether to include user personal data in the initialization process.

**Code Description**: The __init__ function is a constructor method that is called when an instance of the class is created. It initializes various attributes of the instance to default values. The attributes include:

- `name`: A string that is initialized to an empty string, intended to hold the name of the user or instance.
- `user`: A string initialized to an empty string, likely to store user-related information.
- `client`: Initialized to None, this attribute may be used to hold a client object or connection.
- `LLM_url`: A string initialized to an empty string, which is presumably meant to store the URL for a Language Model (LLM) service.
- `LLM_key`: A string initialized to an empty string, intended to hold the API key for accessing the LLM service.
- `model`: A string initialized to an empty string, which may represent the specific model being used.
- `profile`, `setting`, `example`, and `first`: These are multi-line strings initialized to empty values, likely placeholders for additional information or configurations.
- `world`: A string initialized to an empty string, possibly representing a conceptual space or context.
- `world_dict`: An empty dictionary that may be used to store key-value pairs related to the world context.
- `story`: An empty dictionary, likely intended to hold story-related data.
- `history_list`: An empty list that may be used to track historical data or interactions.
- `round`: An integer initialized to 10, which could represent the number of iterations or rounds in a process.
- `result`: An empty list that may be used to store results from operations or computations.
- `input`: An empty list that is likely intended to hold user inputs or data.
- `tools`: An empty list that may be used to store tool objects or references.
- `tool_choice`: A string initialized to "auto", which may indicate the default choice of tool or method.
- `tool`: Initialized to None, this attribute may hold a specific tool object.
- `msg`: Initialized to None, likely intended to store message data.
- `add_msg`: A string initialized to an empty string, which may be used to append additional messages.
- `temperature`: A float initialized to 1, which could be a parameter for controlling randomness in model outputs.
- `access_list`: An empty dictionary that may be used to manage access permissions or user roles.
- `web_search`: A boolean initialized to False, indicating whether web search functionality is enabled.
- `call_robot`: A boolean initialized to True, suggesting that a robot or automated response feature is enabled.
- `user_personal_data`: This attribute is set based on the parameter passed to the function. If `user_personal_data` is True, it initializes a `db` attribute with an instance of `MemoryDataCore`, which likely handles user data storage or retrieval.

**Note**: It is important to ensure that the `user_personal_data` parameter is used appropriately, as it determines whether sensitive user information is included in the instance. Proper handling of this data is crucial for maintaining user privacy and security.
***
### FunctionDef create_socket(self)
**create_socket**: The function of create_socket is to establish a connection with the OpenAI API using the provided API key and base URL.

**parameters**: The parameters of this Function.
· There are no parameters for this function.

**Code Description**: The create_socket function is responsible for initializing a client instance of the OpenAI API. It utilizes the OpenAI class, which is presumably defined in an external library. The function assigns the created client instance to the attribute `self.client`. The initialization requires two attributes from the current object: `self.LLM_key`, which holds the API key necessary for authentication, and `self.LLM_url`, which specifies the base URL for the API endpoint. This setup is essential for any subsequent interactions with the OpenAI services, as it establishes the necessary credentials and connection settings.

**Note**: It is important to ensure that both `self.LLM_key` and `self.LLM_url` are correctly set before calling this function. Failure to do so may result in authentication errors or connection failures when attempting to use the OpenAI client. Additionally, this function does not return any value; its primary purpose is to configure the client for future API calls.
***
### FunctionDef world_add(self, msg)
**world_add**: The function of world_add is to enrich the conversation context by adding relevant information based on the user's message.

**parameters**: The parameters of this Function.
· msg: A list of message dictionaries that contain the conversation history and user input.

**Code Description**: The world_add function is designed to enhance the conversational context by appending relevant information derived from the user's message and other sources. Initially, it sets a base string for the variable `self.world`, which serves as a summary of the conversation's key terms.

The function first checks if the `self.web_search` attribute is enabled. If so, it attempts to perform a web search using an external API. It constructs a payload containing the last message's content, extracts the relevant query, and sends a POST request to the specified URL. If the request is successful, it processes the response to extract the top three search results, appending their names and summaries to `self.world`.

Next, the function iterates through `self.world_dict`, which presumably contains predefined terms and their explanations. It checks the last four messages in `msg` for any matches with the keys in `self.world_dict`. If a match is found, it appends the term and its explanation to `self.world`.

Additionally, if `self.user_personal_data` is enabled, the function adds a section titled "Chat history as follows:" to `self.world`. It searches for similar messages in the database based on the last two messages in `msg`. If any similar records are found, it retrieves the full dialogue associated with the first result and appends it to `self.world`.

The world_add function is called by two other functions within the same class: pr_agent and pr_chat. Both of these functions prepare a list of messages that represent the conversation history and the current user input. After constructing the messages, they invoke world_add to enrich the context before appending the updated `self.world` to the messages list. This integration ensures that the conversational context is continuously updated with relevant information, enhancing the user experience.

**Note**: It is important to handle potential exceptions during the web search and database retrieval processes to avoid breaking the flow of the conversation. Additionally, ensure that the API key and other sensitive information are securely managed to prevent unauthorized access.
***
### FunctionDef func_call(self, msg)
**func_call**: The function of func_call is to process a message and return an additional message based on the provided input.

**parameters**: The parameters of this Function.
· parameter1: msg - An object that contains a function with arguments in JSON format.

**Code Description**: The func_call function is designed to take a single parameter, msg, which is expected to be an object containing a property named __function. This property should have an attribute called arguments, which is a JSON string. The function begins by parsing this JSON string into a Python dictionary using the json.loads method. However, the current implementation does not utilize the parsed arguments in any way. Instead, the function directly returns self.add_msg, which suggests that the function is intended to return a predefined message or object stored in the instance variable add_msg. 

The func_call function is invoked within the pr_agent method of the same class. In this context, it is called when the tool_choice attribute of the instance is set to "none". The pr_agent method constructs a list of messages based on the instance's profile, setting, example, and history. When the tool_choice is "none", it appends the message from self.msg and then calls func_call with the tool object, which is expected to be passed as a parameter. This indicates that func_call is part of a larger messaging framework where it is used to process or generate messages based on the tool's functionality.

**Note**: It is important to ensure that the msg parameter passed to func_call contains the expected structure, particularly the __function.arguments attribute, to avoid potential errors during JSON parsing.

**Output Example**: A possible return value of the func_call function could be the content of self.add_msg, which might look like this: "Message processed successfully."
***
### FunctionDef introduce(self)
**introduce**: The function of introduce is to generate a formatted string that summarizes the introductions of all items in the access list.

**parameters**: The parameters of this Function.
· There are no parameters for this function.

**Code Description**: The introduce function constructs a message by iterating through the access_list attribute of the object. It initializes an empty string variable `msg` to hold the final output. The function then loops through each item in the access_list, which is expected to be a dictionary where each key corresponds to an item and its value is another dictionary containing an 'introduce' key. For each item, the function appends a formatted string to `msg` that includes the item's key and its associated introduction text, followed by a newline character. After completing the loop, the function returns the constructed message string.

**Note**: It is important to ensure that the access_list is properly populated with the expected structure before calling this function, as it relies on the presence of the 'introduce' key in each item's dictionary.

**Output Example**: An example of the possible return value of the function could be:
```
item1: This is the introduction for item1.
item2: This is the introduction for item2.
item3: This is the introduction for item3.
```
***
### FunctionDef pr_agent(self, msg)
**pr_agent**: The function of pr_agent is to manage the conversation flow by processing user messages and enriching the context with relevant historical data and system information.

**parameters**: The parameters of this Function.
· msg: A string representing the user's message that is to be processed.

**Code Description**: The pr_agent function is designed to facilitate interaction within a conversational agent framework. It begins by constructing a list of messages that includes predefined system roles and content, which are derived from the instance's attributes: profile, setting, example, and first message. This establishes the foundational context for the conversation.

The function then iterates through the history_list, which contains previous messages exchanged in the conversation. It appends these messages to the messages list, alternating the role between "user" and "assistant" based on the index of the message. This continues until it reaches the specified round limit, ensuring that only a limited number of historical messages are included to maintain relevance.

Next, the function checks the tool_choice attribute. If tool_choice is set to "none", it appends the current user message and a tool call message generated by invoking the func_call method with the tool object. This indicates that the function is prepared to handle tool interactions when necessary. If tool_choice is not "none", it formats the user message by prefixing it with the user's identifier and appends it to the messages list.

After preparing the messages, the function calls the world_add method, which enhances the conversation context by adding relevant information based on the user's message. This method enriches the messages with additional context, such as web search results and explanations of key terms.

Finally, the function appends the updated world context to the messages list and swaps the last two entries to ensure the most recent context is appropriately positioned. The function concludes by returning the complete messages list, which now contains a comprehensive view of the conversation, including user input and enriched context.

The pr_agent function is invoked within the process method of the same class, specifically when the mode is set to "agent". This integration allows for dynamic message processing and context enrichment, ensuring that the conversational agent can effectively respond to user inputs while maintaining a coherent dialogue history.

**Note**: It is important to ensure that the tool_choice and other instance attributes are correctly set before invoking this function to avoid unexpected behavior. Additionally, the messages list should be managed carefully to prevent exceeding the defined round limit.

**Output Example**: A possible return value of the pr_agent function could look like this:
[
    {"role": "system", "content": "Profile information"},
    {"role": "system", "content": "Current settings"},
    {"role": "system", "content": "Example context"},
    {"role": "system", "content": "First message"},
    {"role": "user", "content": "User: How can I help you?"},
    {"role": "assistant", "content": "Previous assistant response"},
    {"role": "user", "content": "User: What about this topic?"},
    {"role": "tool", "tool_call_id": "tool_id", "content": "Tool function response"},
    {"role": "system", "content": "Enriched context from world_add"}
]
***
### FunctionDef pr_chat(self, msg, set)
**pr_chat**: The function of pr_chat is to facilitate a chat interaction by preparing a structured message history and enriching it with relevant context before sending it for processing.

**parameters**: The parameters of this Function.
· msg: A string representing the user's message to be processed in the chat.
· set: A string indicating the role of the sender, defaulting to "user".

**Code Description**: The pr_chat function is designed to manage the chat interaction by constructing a list of messages that includes the user's input and the conversation history. Initially, it creates a list of messages starting with predefined system messages that contain the user's profile, settings, example, and first message. 

The function then iterates over the history_list, which contains previous messages exchanged in the conversation. It appends each message to the messages list, alternating the role between "user" and "assistant" based on the index of the message. This continues until it reaches the limit defined by the round attribute, ensuring that only a specified number of past messages are included.

After constructing the message history, the function appends the current user message (msg) to the messages list, using the specified role (set). It then calls the world_add function, passing the messages list to enrich the conversation context with additional information relevant to the user's input. The world_add function enhances the messages by appending contextual data, such as web search results and explanations of key terms from the conversation.

Finally, the function appends the enriched world context to the messages list, swaps the last two entries to maintain the correct order, and returns the complete messages list. 

The pr_chat function is invoked by the process function when the mode is set to "chat". This integration allows for a seamless flow of conversation, where the user's input is processed, and the context is continuously updated, enhancing the overall user experience.

**Note**: It is important to ensure that the messages list is constructed correctly and that the world_add function is able to enrich the context without errors. Proper handling of the conversation history is crucial to maintain coherence in the chat interaction.

**Output Example**: 
A possible return value of the pr_chat function may look like this:
```
[
    {"role": "system", "content": "User Profile Information"},
    {"role": "system", "content": "User Settings Information"},
    {"role": "system", "content": "Example Message"},
    {"role": "system", "content": "First Message"},
    {"role": "user", "content": "Hello, how can I help you today?"},
    {"role": "assistant", "content": "I am here to assist you with your queries."},
    {"role": "system", "content": "Enriched context from world_add function."}
]
```
***
### FunctionDef add_data(self)
**add_data**: The function of add_data is to store user dialogue history into a database if user personal data is available.

**parameters**: The parameters of this Function.
· None

**Code Description**: The add_data function is responsible for managing and storing the dialogue history of a user. It first checks if there is any user personal data available. If such data exists, it retrieves the last two entries from the history_list, which contains the dialogue exchanges. These entries are formatted into a dictionary that includes the role of the speaker, the content of the dialogue, and a timestamp indicating when the data was recorded.

The formatted dialogue is then inserted into a database using the insert_dialogues method of the db object. The result of this insertion operation is printed to the console for verification. After the data has been successfully added to the database, the function removes the first two entries from the history_list to maintain a manageable size of stored dialogues.

This function is called within the generate_content function, which is part of the process method in the same module. The generate_content function is responsible for processing the responses from a chat completion API. It appends user messages and generated responses to the history_list. If the number of entries in the history_list exceeds a certain threshold (defined by the round attribute), the add_data function is invoked to store the oldest dialogues in the database, ensuring that the history_list does not grow indefinitely.

**Note**: It is important to ensure that user_personal_data is properly managed and that the database connection is established before calling this function. Additionally, the history_list should be maintained correctly to prevent any potential data loss or inconsistency.
***
### FunctionDef process(self, msg, mode, tool, stream)
**process**: The function of process is to handle user messages and manage interactions based on different operational modes, facilitating communication through a chat completion API.

**parameters**: The parameters of this Function.
· msg: A string representing the user's message to be processed.
· mode: A string indicating the operational mode for processing the message, defaulting to "chat".
· tool: A list of tools to be used in the processing, defaulting to an empty list.
· stream: A boolean indicating whether to stream the response or not, defaulting to False.

**Code Description**: The process function is a central component designed to manage the interaction flow based on the specified mode. It begins by initializing an empty list called messages, which will be populated based on the mode of operation.

1. **Tool Mode**: If the mode is set to "tool", the function prepares to utilize specified tools. It sets the tool_choice to "required" and temperature to 0, indicating a deterministic response. The user message is wrapped in a dictionary format and sent to the chat completion API. The response is processed to extract any tool calls, and if successful, it constructs a function call string with the extracted arguments. If no tool calls are found, it defaults to returning a chat response.

2. **Agent Mode**: When the mode is "agent", the function sets the tool_choice to "auto" and temperature to 1.1. It prefixes the user message with the user's identifier and calls the pr_agent function to enrich the message context with historical data and system information.

3. **Chat Mode**: In "chat" mode, the function sets the tool_choice to "none" and temperature to 1.3. Similar to the agent mode, it prefixes the user message and calls the pr_chat function to prepare the message history for processing.

4. **Report Mode**: The "report" mode operates similarly to chat mode, focusing on processing the message without tool interactions.

5. **Solo Mode**: In "solo" mode, the function allows for direct message input, either as a list or a single string. It prints the messages for debugging purposes.

6. **Spot Mode**: The "spot" mode initializes the messages list with predefined system messages, including user profile, settings, and examples, along with the user message.

After preparing the messages based on the selected mode, the function calls the chat completion API to generate a response. If streaming is enabled, it defines a generator function to yield response chunks as they arrive, allowing for real-time interaction. The history_list is updated with the user message and the generated response, and if the token count exceeds a threshold, it adjusts the round attribute to manage the history size.

If streaming is not enabled, the function processes the response to extract the content and updates the history_list accordingly. It also manages the addition of any supplementary messages and ensures that the history remains within the defined limits.

The process function integrates multiple helper functions, including pr_agent and pr_chat, to facilitate dynamic message processing and context enrichment, ensuring coherent dialogue management throughout the interaction.

**Note**: It is crucial to ensure that the mode is correctly set and that the necessary instance attributes are initialized before invoking this function to avoid unexpected behavior. The messages list should be managed carefully to maintain coherence in the conversation.

**Output Example**: A possible return value of the process function could look like this:
```
"Here is the response generated based on your input."
```
#### FunctionDef generate_content
**generate_content**: The function of generate_content is to process responses from a chat completion API and manage the dialogue history.

**parameters**: The parameters of this Function.
· None

**Code Description**: The generate_content function is designed to handle the generation of content based on responses received from a chat completion API. It initializes an empty string `p` to accumulate the generated content and a variable `token` to track the total number of tokens used in the conversation. The function iterates over a collection `R`, which is expected to contain response chunks from the API.

During each iteration, the function appends the content of the first choice from the current chunk to the string `p` and yields this content, allowing for real-time processing of the generated text. If the finish reason of the current chunk indicates that the generation has stopped (i.e., `finish_reason` is "stop"), the function updates the `token` variable with the total number of tokens used in that chunk.

After processing the chunks, the function appends the current message (`msg`) and the accumulated content (`p`) to a list called `history_list`, which is used to maintain a history of the dialogue. The function then checks if the total number of tokens exceeds a threshold of 4800. If it does, it reduces the `round` attribute by half (adjusting for odd numbers), which determines how many entries are kept in the `history_list`. If the token count is below the threshold, it increases the `round` by 2.

To ensure that the `history_list` does not grow indefinitely, the function enters a loop that calls the `add_data` method to remove the oldest entries from the list if its length exceeds the current value of `round`. This helps maintain a manageable size of stored dialogues.

The `add_data` function, which is called within `generate_content`, is responsible for storing the user dialogue history into a database if user personal data is available. It retrieves the last two entries from `history_list`, formats them, and inserts them into the database. This ensures that the dialogue history is preserved and managed effectively.

**Note**: It is crucial to ensure that the `history_list` is maintained correctly to prevent data loss or inconsistency. Additionally, the management of user personal data should comply with relevant data protection regulations.

**Output Example**: A possible return value of the function could be a string containing the accumulated content from the API responses, such as: "Hello, how can I assist you today?"
***
***
