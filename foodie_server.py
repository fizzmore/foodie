from fastmcp import FastMCP
from foodie.tools.map_tool import create_static_map
from foodie.tools.rec_tool import search_web, get_info


mcp = FastMCP(
    name="Foodie Server",
    instructions="""
        This server provides recommendation of restaurant for a given location and provide map link.
        
        Step 1: When user ask about restaurant recommendation, 
        check if location is provided. If it is not provided, ask user back.
        Use recommend_restaurant method to get recommendations.
        It will be in json format for restaurant reviews / recommendations.
        
        Step 2: Based on the web results from Step 1, 
        do simple research on each restaurant using research_recommendation method.
        The job of research_recommendation is to extract restaurant name and address.
        It should also provide the reason why it should be recommended
         
        Step 3. Combine addresses from Step 2 (concatenate addresses separated by | (pipe string)) 
        Use build_map method to create one map including multiple locations.  
    """,
)



@mcp.tool(
    description="""
    Find and recommend restaurants in a specific location.
    """,
)
def recommend_restaurant(location, cuisine=None, top_n=5):
    return search_web(location, cuisine=cuisine, top_n=top_n)


@mcp.tool(
    description="""
    Research restaurant to get address information and why it is selected as recommendation
    Address should include street address, state code and zip code.
    Other information on the famous dishes for the restaurant would help providing rationale for recommendation
    """,
)
def research_restaurant(restaurant_name, location):
    return get_info(restaurant_name, location)


@mcp.tool(
    description="""
    Generate static maps from restaurant addresses. 
    Use this for restaurant location requests, dining recommendations, or 
    finding places to eat in specific areas.
    Input should be string for addresses separated by | (pipe string).
    file_name should be summary of what user requested for.
    For instance, if users asked about korean restaurant in new york,
    The title would be korean-new-york, so that we understand what was requested.
    """
)
def build_map(addresses, file_name) -> dict:
    return create_static_map(addresses, file_name=file_name)


if __name__ == "__main__":
    mcp.run(transport='stdio')