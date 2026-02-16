# Appointment script – APEN (e.g. uniform collection / récupération de tenues)

**Version:** 1.0 – MVP

---

## Flow

1. Confirm intent: "Souhaitez-vous prendre rendez-vous pour une récupération de tenue ou un autre motif ?"
2. Ask site preference if multiple: "Quel site vous convient : Paris Montrouge, Le Havre, Reims, Nancy ou Nantes ?"
3. Ask availability: "Quel jour souhaitez-vous ? Avez-vous un créneau préféré, matin ou après-midi ?"
4. Propose slot(s) from calendar (e.g. "Je peux vous proposer mardi 18 février à 10h ou 14h. Laquelle vous convient ?")
5. Confirm: "Parfait, je vous inscris [date] à [heure] pour [motif]. Pouvez-vous me donner votre nom et un numéro de téléphone pour confirmation ?"
6. Create calendar event and confirm: "Votre rendez-vous est enregistré. Vous recevrez une confirmation par e-mail si vous l’indiquez."

---

## French prompts (agent)

- "Pour quel motif souhaitez-vous ce rendez-vous ? Récupération de tenue, visite, autre ?"
- "Quel est votre nom, s’il vous plaît ?"
- "Un numéro de téléphone pour la confirmation ?"
- "Votre adresse e-mail pour l’envoi de la confirmation ?" (optional)

---

## English prompts

- "What is the reason for this appointment? Uniform collection, visit, other?"
- "May I have your name?"
- "A phone number for confirmation?"
- "Your email for the confirmation?" (optional)
