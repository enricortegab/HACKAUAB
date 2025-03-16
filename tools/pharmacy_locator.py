from llm import llm
from langchain.tools import Tool

def pharmacy_locator(location: str):
    """
    Takes the location of the user and returns the closest pharmacy to the client.
    """
    prompt = f"""
    You are an AI that knows were all the pharmacies that are available at each location.
    Given the following location, give the address of a pharmacy near that and their schedule.
    If the user wants to buy the medication online, dont go here, activate the medication tool by returning the dictionary.

    Location: {location}
    """
    response = llm.invoke(prompt)
    return response

pharmacy_locator_tool = Tool(
    name="Pharmacy_Locator_Tool",
    func=pharmacy_locator,
    description="Takes the location of the user and returns the closest pharmacy to the client."
)
