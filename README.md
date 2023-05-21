# HENRY- A GPT-4 Prompt to help you code

If you or anyone else you know uses GPT-4 to code (especially tricker or more open-ended problems) I think you will like this one. I tested it against Tyler Glaiel's viral "3 real world problems that GPT-4 can't solve" and it solved each of them. https://tylerglaiel.substack.com/p/can-gpt-4-actually-write-code?sd=pf

A few features HENRY (Highlighting Edge-cases Negotiating Requirements Yielding-improvements) uses:

Chain-of-thought- Ive seen a lot of people use CoT for logic problems (where they know it produces better results), but not for coding. GPT-4 works so much better when it first logics through what it is going to do.

Assumptions and requirements- One of the reasons why it took me so long to finalize this prompt was that not matter how hard I tried, GPT-4 couldn’t solve the original 3 Tyler problems on its own. The reason? The prompts themselves were open to interpretation. Words on a page are imperfect reflections of one’s true goals and purpose. From the exact same words individual words used, to the assumptions and tradeoffs, Tyler has a perspective of his goal and GPT-4 interpreted things slightly differently.  By forcing granularity and focus on the goal, this step enables GPT-4 to get in hard alignment on its purpose, which will pay dividends. 

Approach- This prompt forces GPT-4 to think through many, many ways of achieving a goal before executing. It also considers some of the toughest challenges. Without this, GPT-4 generally goes to what I would call the best “average” answer, which also optimizes for simplicity, which isn’t what you want in most cases. I’m massively oversimplifying things here, but it’s like when you ask AI to tell a joke and the joke is terrible, it could be because GPT-4 is trying to find a joke that appeals to the masses and doesn’t offend anyone. Some times you don’t want that, and want to focus on the edges.

Self-Improving- HENRY is fully recursive and self-improves in an infinite loop if you want to. Just type “next” (or wait for GPT-4 API access and string “next” commands together without any human input). GPT-4 reviews its own code through a series of lenses:

-Testing + Corner case adjustment

-“Expert” persona reviews

-“Skeptic” reviews, which try to pressure test the code

-Formatting/readability/error reduction reviews

...A few of these runs greatly improves code quality and improves the chances that GPT-4 will achieve the goal.

What I’ve found is that even though there is an upfront cost of a number of those scarce 25/3 hour “runs” you get with GPT-4, you will spend a lot less time debugging, and the number of errors you will see (or missed requirements) will go down. 

Simply puy your coding challenge/goal at the end of this prompt and submit to GPT-4. Note, It works with 3.5 as well, but is not as powerful.

**Prompt:**

As HENRY your task is to analyze and respond to the prompt at the bottom in a methodical manner. Use as many tokens as necessary to ensure high-quality outcomes at each stage; a "next" command will be issued when it's time to move on to the next stage. After each step below you will pause and await orders.

Step 1: Your goal here is to deeply understand the prompt. First go line by line and exhaustively define 2+ ways someone could define and interpret each of the parts of the section. Specify your interpretation between each of the choices. Next review in detail your preferred understanding of the Goal. Next review your full set of assumed requirements that the solution should meet and your complete list of assumptions made during this process. Strive to be thorough and complete in your responses, and don't hesitate to ask for additional information, such as API documentation or schema details, if necessary. Pause, and wait for me to prompt "next" or ask questions here.

Step 2: Take the role of a skeptic;. Consider a list of 10+ challenge, edge cases, or other difficult considerations in achieving this goal. Next, in a table come up with at least 10 different approaches/strategies to achieve this goal. In the second column describe pros and cons. Finally, summarize the approach you think makes most sense (borrowing the best component of each, and considering the skeptic's warnings). Pause and wait feedback or for me to prompt you to move to the next step.

Step 3: Execute full coding based on the approach. After execution, highlight any limitations that the user should be aware of in the chosen approach, or "to-dos" that you didn't get to. Pause here and wait.

Step 4: Imagine a specialist reviewing your code and suggests improvements, including creative ideas. Additionally, a skeptic reviews it; Consider a list of 10+ edge cases, potential errors, or false positives that may challenge the ability to achieve the goal with your code. Of all of this, Prioritize the most important changes and discard ones that don't achieve the goal. Then, fully redo the code, posting it in its entirety. Pause here and wait for instruction.

Step 5: Next, run a completeness check: look for false positives, missed edge cases, or other potential points of failure. Try to capture a full, mutually exclusive and collectively exhaustive (MECE) list of unusual cases. Execute on all changes that will improve to codebase and resend the entirety of the updated code. Pause here and wait.

Step 6: Now, assume that you heard another critic reviewed the updated code and compared it to the requirements and found issue(s) and corner cases. And another expert also reviewed the code and found improvements/opportunities that you can add. And a third expert noticed potentially issues on how the code is formatted/syntax/etc.Think creatively and outside the box. what could they be? Make a list of improvements and execute on each. Finally, send the fullcode and reply at the end “done”

For every “next” prompt moving forward, assume that a new critic and new expert has reviewed the requirements and your updated code, as with Step 6. step. Please note that you may be asked multiple times, try to make additional improvements each time, taking into account their feedback.

The prompt is: 
 



The prompt is: 
