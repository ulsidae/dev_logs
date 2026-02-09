# 🍯 Chat Prototype 

**Designing a Conversational Algorithm Using Numerical Approximation Concepts** *(A Reconstruction of a High School Research Project)*

---

## 📌 Project Overview
This project is an **idea-oriented prototype**. 
While working on an AI project in the past, I faced the challenge of accurately identifying user intent within a limited dataset. To solve this, I drew inspiration from the **Newton-Raphson method** in numerical analysis.

- Just as numerical analysis finds the roots of complex functions through iterative approximation, this system scans for key terms to **approximate the correct answer category**.
  
- **Note:** This is a **proof-of-concept prototype** created to demonstrate the conceptual link between mathematical approximation and intent classification. Actual numerical calculus is not implemented in the code.

---

## 💡 Concept
1. **Keyword Extraction:** The system scans the input for specific predefined keywords.
2. **Intent Approximation:** If keywords exist, it assumes the input has "approximated" a valid query and triggers the corresponding response.
3. **Analogy:** This mimics the way the Newton-Raphson method converges on a solution, applied here to the logic of **intent mapping**.

```javascript
// Conceptual function using the idea of 'Approximation'
function calculateNewton(input){  
  const keys = ["weather", "temperature", "humidity", "temp"];  
  let x = keys.filter(k => input.toLowerCase().includes(k)).length;  
  return x >= 1; // If keywords are found, it has 'converged' on a solution.
}
```
🖥️ HTML/JS Prototype
​A simple chat UI that responds to user inquiries based on keyword proximity.

<img src="https://github.com/ulsidae/dev_logs/blob/main/AI/Newton-Raphson/XD.PNG" height="400"/>

• ​Demo: 🍯 [HTML](https://github.com/ulsidae/dev_logs/blob/main/AI/Newton-Raphson/example.html)

​You can use it like:
```javascript
const weatherData = {weather: "Sunny", temp: "18°C", humidity: "40%"};  
  
function sendMessage(){  
  const i = document.getElementById('user-input');  
  const t = i.value;  
  if(!t) return;  
  
  addMsg(t, 'user');  
  i.value = '';  
  
  setTimeout(() => {  
    const res = calculateNewton(t) ?  
      `Today's weather is ${weatherData.weather}, temperature is ${weatherData.temp}.` :  
      "Newton-Raphson couldn't find a solution. (Missing keywords)";  
    addMsg(res, 'bot');  
  }, 400);  
}  
```
## 💡 Key Insights

• ​Newton-Raphson Analogy: Numerical Approximation → Keyword Presence Validation.

• ​Intent Approximation: Focusing on core information retrieval from user input.

• ​Purpose: Demonstrating creative problem-solving and the ability to bridge mathematical concepts with software logic.


## 🔹 Note​

>This project values the originality of the approach over technical complexity. It serves as a record of my intellectual curiosity and experimental logic during my >high school years.
