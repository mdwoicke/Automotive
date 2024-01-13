import autogen
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from inventory import get_inventory

config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")

config_list_4v = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-vision-preview"],
    },
)

llm_config = {"config_list": config_list}

get_inventory_declaration = {
    "name": "get_inventory",
    "description": "Retrieves the inventory details for a specified spare part."
}


def is_termination_msg(data):
    has_content = "content" in data and data["content"] is not None
    return has_content and "TERMINATE" in data["content"]


user_proxy = autogen.UserProxyAgent(
    'user_proxy',
    is_termination_msg=is_termination_msg,
    system_message="You are the boss",
    human_input_mode='NEVER',
    function_map={"get_inventory": get_inventory}
)

damage_analyst = MultimodalConversableAgent(
    name="damage_analyst",
    system_message="As the Damage Analyst, your role is to accurately describe the contents of the image provided. Respond only with what is visually evident in the image, without adding any additional information or assumptions.",
    llm_config={"config_list": config_list_4v, "max_tokens": 300}
)

inventory_manager = autogen.AssistantAgent(
    name="inventory_manager",
    system_message="An inventory management specialist, this agent accesses the inventory database to provide information on the availability and pricing of spare parts.",
    llm_config={"config_list": config_list,
                "functions": [get_inventory_declaration]}
)

customer_support_agent = autogen.AssistantAgent(
    name="customer_support_agent",
    system_message="An agent adept in email composition, tasked with drafting and sending client messages following confirmation of inventory and pricing details. It signals task completion by responding with 'TERMINATE' after the email is sent.",
    llm_config=llm_config
)

groupchat = autogen.GroupChat(
    agents=[user_proxy, damage_analyst, inventory_manager,
            customer_support_agent], messages=[]
)

manager = autogen.GroupChatManager(
    groupchat=groupchat, llm_config=llm_config
)

user_proxy.initiate_chat(
    manager, message="""
        Process Overview:
        Step 1: Damage Analyst identifies the car brand and the requested part from the customer's message and image.
        Step 2: Inventory Manager verifies part availability in the database.
        Step 3: Customer Support Agent composes and sends a response email to the customer.

        Customer's Message: 'My Display has been stolen, do you have them in stock?'
        Image Reference: [Tesla Display Image](https://custom-tesla.com/cdn/shop/products/image_1445x.heic?v=1665410372)
    """, clear_history=True
)
