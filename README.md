# CONORGPT- Prompt to help you code

Optimized coding prompt for GPT-4 to help build applications and help you code
CONOR (Continuous Optimization of Needs and Requirements) reduces hallucinations and error rates and self-improves its own code. Solves some of the most challenging coding challenges with minimial human input.  

**Prompt:**

Your task is to analyze and respond to the prompt at the bottom in a methodical manner. Use as many tokens as necessary to ensure high-quality outcomes at each stage; a "next" command will be issued when it's time to move on to the next stage. After each step below you will pause and await orders.

Step 1: Your goal is to deeply understand the prompt. First go line by line and exhaustively define 2+ ways someone could define and interpret each of the parts of the section. Next review in detail your preferred interpretation of the prompt. Next review your full set of assumed requirements that the solution should meet and your complete list of assumptions  made during this process. Strive to be thorough and complete in your responses, and don't hesitate to ask for additional information, such as API documentation or schema details, if necessary.  Pause, and wait for me to prompt "next" or ask questions here. 

Step 2: Take the role of a skeptic;. Consider a list of 10+ challenge, edge cases, or other difficult considerations in achieving this goal. Next, come up with at least 5 different approaches/strategies to achieve this goal.  Finally, summarize the approach you think makes most sense (borrowing the best component of each, and considering the skeptic's warnings). Pause and wait feedback or for me to prompt you to move to the next step.

Step 3: Execute full coding based on the approach.  After execution, highlight any limitations that the user should be aware of in the chosen approach, or "to-dos" that you didn't get to. Pause here and wait. 

Step 4: Imagine a specialist reviewing your code and suggests improvements, including creative ideas. Additionally, a skeptic reviews it; Consider a list of 10+ edge cases, potential errors, or false positives that may challenge the ability to achieve the goal with your code. Of all of this, Prioritize the most important changes and discard ones that don't achieve the goal. Then, fully redo the code, posting it in its entirety. Pause here and wait for instruction. 

Step 5: Next, run a completeness check: look for false positives, missed edge cases, or other potential points of failure. Try to capture a full, mutually exclusive and collectively exhaustive (MECE) list of unusual cases. Execute on all changes that will improve to codebase and resend the entirety of the updated code. Pause here and wait. 

Step 6: Now, assume that you heard another critic reviewed the updated code and compared it to the requirements and found issue(s) and corner cases. And another expert also reviewed the code and found improvements/opportunities that you can add. And a third expert noticed potentially issues on how the code is formatted/syntax/etc.Think creatively and outside the box. what could they be? Make a list of improvements and execute on each. Finally, send the fullcode and reply at the end “done”

For every  “next” prompt moving forward, assume that a new critic and new expert has reviewed the requirements and your updated code, as with Step 6. step. Please note that you may be asked multiple times, try to make additional improvements each time, taking into account their feedback. 

The prompt is: 
A crescent moon can be defined as the difference between 2 circles. In code it can be stored in a struct like so: struct crescent { float outer_circle_x, outer circle_y, outer_circle_radius; float inner_circle_x, inner_circle_y, inner_circle_radius; }; write a collision detection algorithm that takes 2 crescents and returns true if they overlap and false if they don't
