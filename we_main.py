from weather_main import create_weather_agent
import sys
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()

def print_welcome():
    """Print welcome message with examples."""
    print(Style.BRIGHT + Fore.CYAN + "="*60)
    print(Fore.MAGENTA + "🌤️  Welcome to the Intelligent Weather Agent! 🌤️")
    print(Style.BRIGHT + Fore.CYAN + "="*60)
    print(Fore.WHITE + "\nI can help you with various weather queries like:")
    print(Fore.YELLOW + "• 'What's the weather today?'")
    print(Fore.YELLOW + "• 'Will it rain tomorrow in Dhaka?'")
    print(Fore.YELLOW + "• 'Was it sunny yesterday?'")
    print(Fore.YELLOW + "• 'What's the temperature in London?'")
    print(Fore.YELLOW + "• 'Do I need an umbrella this afternoon?'")
    print(Fore.YELLOW + "• 'Weather forecast for this weekend'")
    print(Fore.YELLOW + "• 'Compare temperature today vs tomorrow'")
    
    print(Fore.GREEN + "\nSupported locations: Any city worldwide!")
    print(Fore.GREEN + "Supported times: Today, tomorrow, yesterday, specific dates")
    print(Fore.GREEN + "Weather data: Temperature, rain, wind, humidity, and more!")
    
    print(Fore.WHITE + "\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print(Fore.WHITE + "Type 'help' to see this message again.")
    print(Style.BRIGHT + Fore.CYAN + "="*60 + "\n")


def print_help():
    """Print help information."""
    print(Fore.CYAN + "\n📖 Weather Agent Help:")
    print(Fore.WHITE + "Here are some example queries you can try:")
    
    examples = [
        "Current weather: 'What's the weather now?'",
        "Specific location: 'Weather in Tokyo'", 
        "Future forecast: 'Will it rain tomorrow?'",
        "Historical data: 'Was it hot yesterday in Dubai?'",
        "Time-specific: 'Temperature this morning in Paris'",
        "Planning: 'Should I carry umbrella this evening?'",
        "Comparison: 'Compare today's weather with tomorrow'",
        "Weekend plans: 'Weather forecast for this weekend'"
    ]
    
    for i, example in enumerate(examples, 1):
        print(Fore.YELLOW + f"{i}. {example}")
    
    print(Fore.GREEN + "\nThe agent is smart and can understand natural language!")
    print(Fore.GREEN + "Just ask your weather question in plain English.\n")


def main():
    """Main function to run the weather agent."""
    try:
        print_welcome()
        
        # Create weather agent instance
        
        # Interactive loop
        while True:
            try:
                # Get user input
                print(Fore.BLUE + "🔄 Initializing Weather Agent...")
                model = "llama-3.3-70b-versatile"
                agent = create_weather_agent(model)
                print(Fore.GREEN + "✅ Weather Agent ready!\n")
                
                user_query = input(Fore.WHITE + Style.BRIGHT + "You: " + Style.RESET_ALL).strip()
                
                # Handle exit commands
                if user_query.lower() in ["exit", "quit", "bye", "q"]:
                    print(Fore.MAGENTA + "\n👋 Thanks for using Weather Agent! Stay safe and have a great day!")
                    break
                
                # Handle help command
                if user_query.lower() in ["help", "h", "?"]:
                    print_help()
                    continue
                
                # Handle empty input
                if not user_query:
                    print(Fore.YELLOW + "Please ask me a weather question!")
                    continue
                
                # Process the weather query
                print(Fore.BLUE + "\n🤖 Weather Agent: ", end="")
                print(Fore.CYAN + "Thinking...")
                
                response = agent.process_weather_query(user_query)
                
                # Display response
                print(Fore.GREEN + "🌟 Weather Agent: " + Fore.WHITE + response + "\n")
                
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n⚠️  Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(Fore.RED + f"\n❌ Error processing query: {str(e)}")
                print(Fore.YELLOW + "Please try asking your question differently.\n")
    
    except Exception as e:
        print(Fore.RED + f"❌ Failed to initialize Weather Agent: {str(e)}")
        print(Fore.YELLOW + "Please check your internet connection and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()