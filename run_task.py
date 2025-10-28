import asyncio
import sys
import json
import speech_recognition as sr


from agents.intent_parser import parse_command
from Automation.browser_executor import execute_actions


def get_user_command():
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    else:
        choice = input(" Press V for voice command or Enter to type: ").strip().lower()
        if choice == "v":
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print(" Listening...")
                audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio)
                print(f" You said: {command}")
                return command
            except sr.UnknownValueError:
                print(" Could not understand audio.")
                return input("Type your command instead: ")
        else:
            return input("What do you want to do? ")



async def main():
    # Check for required environment variables
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    if "book" in " ".join(sys.argv[1:]).lower() and (not os.getenv('MMT_EMAIL') or not os.getenv('MMT_PASSWORD')):
        print("\n❌ Error: For flight bookings, please set MMT_EMAIL and MMT_PASSWORD in your .env file")
        return
    
    command = get_user_command()
    print(f"\n🧠 Understanding command: {command}")

    # Parse intent into JSON plan
    parsed = parse_command(command)
    if parsed is None:
        print("\n❌ Could not create action plan. Please try again with more specific details.")
        return

    print("\n📋 Action Plan:")
    print(json.dumps(parsed, indent=2))  # Pretty print JSON plan

    confirm = input("\n⚡ Proceed with execution? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Cancelled.")
        return

    # Execute JSON actions in browser
    print("\n🚀 Executing actions...")
    try:
        await execute_actions(parsed)
        print("\n✅ Actions completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        return


if __name__ == "__main__":
    asyncio.run(main())
