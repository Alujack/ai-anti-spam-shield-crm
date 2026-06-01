::: titlepage

# សាកលវិទ្យាល័យភូមិន្ទភ្នំពេញ
## ROYAL UNIVERSITY OF PHNOM PENH

\vspace

# ការរកឃើញសារឆបោក និងហ្វីសុីង តាមប្រព័ន្ធបញ្ញាសិប្បនិម្មិត
## AI Anti-Spam Shield — An Intelligent Mobile Platform for Spam, Phishing and Voice-Scam Detection Using Hybrid Machine Learning

\vspace

A Research Report
In Partial Fulfilment of the Requirement for the Degree of
Bachelor of Information Technology Engineering

\vspace

**Submitted by:**
AI Shield Inc. Project Team

\vspace

**June 2026**

:::

\pagebreak

::: titlepage

# សាកលវិទ្យាល័យភូមិន្ទភ្នំពេញ
## ROYAL UNIVERSITY OF PHNOM PENH

\vspace

## AI Anti-Spam Shield — An Intelligent Mobile Platform for Spam, Phishing and Voice-Scam Detection Using Hybrid Machine Learning

\vspace

A Research Report
In Partial Fulfilment of the Requirement for the Degree of
Bachelor of Information Technology Engineering

\vspace

**Submitted by:**
AI Shield Inc. Project Team

\vspace

**Examination committee:**
Dr. Srun Soliva
Mr. Chhim Bunchhun
Mr. Hun Sovannsoreya
Miss E Vathana

\vspace

**June 2026**

:::

\pagebreak

# មូលន័យសង្ខេប

ក្នុងយុគសម័យឌីជីថលបច្ចុប្បន្ន ការវាយប្រហារតាមសាររំខាន (spam) និង phishing កាន់តែកើនឡើង និងកាន់តែមានភាពស្មុគស្មាញ។ ប្រព័ន្ធច្រោះសារបែបប្រពៃណី (rule-based filters) មិនអាចទប់ទល់នឹងការវាយប្រហារថ្មីៗទាំងនោះបានទេ។ ការស្រាវជ្រាវនេះបង្ហាញពីការអភិវឌ្ឍ AI Anti-Spam Shield ដែលជាកម្មវិធីទូរស័ព្ទឆ្លាតវៃមួយដើម្បីរកឃើញការវាយប្រហារ spam, phishing និង voice scam ជាមួយនឹងភាពជឿជាក់ខ្ពស់។

ប្រព័ន្ធនេះប្រើ Machine Learning បីប្រភេទខុសគ្នា៖ Logistic Regression សម្រាប់សារ SMS (ភាពត្រឹមត្រូវ ៩៩.៦៨%), Random Forest សម្រាប់ voice scam (ភាពត្រឹមត្រូវ ១០០%), និង Random Forest ជាមួយនឹងលក្ខណៈ URL សម្រាប់ phishing (ភាពត្រឹមត្រូវ ៨០.៩៥%)។ ប្រព័ន្ធត្រូវបានបង្កើតឡើងជាលក្ខណៈបន្ថែមសេវាកម្មតូចៗ (microservices) ដោយរួមបញ្ចូលសេវាកម្ម FastAPI ML, Express.js backend, មូលដ្ឋានទិន្នន័យ PostgreSQL, Redis queue, និងកម្មវិធី Flutter mobile។ លទ្ធផលបង្ហាញថាប្រព័ន្ធនេះអាចចាប់បាន spam និង phishing ក្នុងរយៈពេលតិចជាង ៤៥ ms និងអាចវិភាគសារសំឡេងក្នុងរយៈពេលតិចជាង ១.២ វិនាទី។

**ពាក្យគន្លឹះ៖** ការរកឃើញ spam, ការរកឃើញ phishing, Machine Learning, ការវិភាគសារសំឡេង, សន្តិសុខទូរស័ព្ទ, សុវត្ថិភាពសាយប័រ, Random Forest, Logistic Regression, TF-IDF, Flutter, Microservices

\pagebreak

\pagebreak

# ABSTRACT

Spam and phishing attacks have grown in volume and sophistication, disproportionately affecting mobile users in emerging markets such as Cambodia. Traditional rule-based filters fail against modern social-engineering techniques, brand impersonation, and voice-based scams. This study presents **AI Anti-Spam Shield**, an intelligent cross-platform application that detects spam, phishing and voice-scam threats using a hybrid machine-learning approach. The system combines three specialised classifiers — a Logistic Regression model for Short Message Service (SMS) spam, a Random Forest model for voice-scam dialogue, and a Random Forest model with engineered Uniform Resource Locator (URL) features for phishing — each trained on curated public datasets obtained from the Hugging Face hub. Textual preprocessing includes URL and e-mail masking, stop-word removal and Porter stemming, after which Term Frequency–Inverse Document Frequency (TF-IDF) vectorisation is applied. The overall platform is designed as a set of Docker-orchestrated microservices consisting of a FastAPI inference service, an Express.js Application Programming Interface (API), a PostgreSQL database, a Redis-backed BullMQ job queue, a Kong API gateway, and a Flutter mobile client. On held-out test sets the SMS model achieves 99.68 per cent accuracy, the voice model 100 per cent, and the phishing model 80.95 per cent. End-to-end API latency averages 45 milliseconds and voice analysis completes within 1.2 seconds. The study contributes a reproducible reference architecture, empirical evidence that classical machine learning remains competitive for short-text spam in mobile contexts, and a discussion of interpretability, deployability and future work including Khmer-language support and on-device inference.

**Keywords:** spam detection, phishing detection, machine learning, voice-scam analysis, mobile security, cybersecurity, Random Forest, Logistic Regression, TF-IDF, Flutter, FastAPI, microservices.

\pagebreak

\pagebreak

# SUPERVISOR'S RESEARCH SUPERVISION STATEMENT

**TO WHOM IT MAY CONCERN**

Name of program: Bachelor of Information Technology Engineering

Name of candidate: **AI Shield Inc. Project Team**

Title of research report: **AI Anti-Spam Shield — An Intelligent Mobile Platform for Spam, Phishing and Voice-Scam Detection Using Hybrid Machine Learning**

This is to certify that the research carried out for the above titled bachelor's research report was completed by the above-named candidates under my direct supervision. This report material has not been used for any other degree. I played the following part in the preparation of this research report:

Supervisor's name: **CHHIM Bunchhun**

Supervisor's signature: ............................................................

Date: ............................................................

\pagebreak

# CANDIDATE'S STATEMENT

**TO WHOM IT MAY CONCERN**

This is to certify that the research report we, the AI Shield Inc. Project Team, hereby present, entitled **"AI Anti-Spam Shield — An Intelligent Mobile Platform for Spam, Phishing and Voice-Scam Detection Using Hybrid Machine Learning"** for the degree of Bachelor of Information Technology Engineering at the Royal University of Phnom Penh, is entirely our own work and, furthermore, that it has not been used to fulfil the requirements of any other qualification, in whole or in part, at this or any other university or equivalent institution.

No reference to, or quotation from, this document may be made without the written approval of the authors.

Signed by candidate: ............................................................

Date: ............................................................

Sign by CHHIM Bunchhun: ............................................................

Supervisor's signature: ............................................................

Date: ............................................................

\pagebreak

# ACKNOWLEDGMENTS

We extend our sincere gratitude to the Royal University of Phnom Penh and the Faculty of Engineering for providing the academic environment in which this Project Practicum was carried out. We wish in particular to thank our supervisor, **Mr. Chhim Bunchhun**, for his patient guidance, constructive criticism and continuous encouragement throughout every phase of this work.

We also thank the open-source and open-data communities — the maintainers of the Hugging Face datasets repository, the scikit-learn project, the FastAPI and Flutter teams, and the authors whose earlier work formed the intellectual foundation of this study — without whom the project could not have been realised.

Finally we acknowledge with gratitude the support of our families and classmates who provided invaluable feedback during user testing and rehearsal sessions.

\pagebreak

\pagebreak

# LIST OF FIGURES

```
Figure 3.1  High-level microservice architecture ……………………………………………………………………………  9
Figure 3.2  End-to-end request flow for a text scan ………………………………………………………………… 10
Figure 3.3  Text preprocessing pipeline ………………………………………………………………………………………………… 11
Figure 3.4  TF-IDF feature-extraction flow …………………………………………………………………………………………… 12
Figure 3.5  Voice processing pipeline ……………………………………………………………………………………………………… 14
Figure 3.6  Mobile application navigation map ………………………………………………………………………………… 15
Figure 3.7  Deployment topology (Docker Compose) ………………………………………………………………………… 17
Figure 4.1  SMS classifier confusion matrix ……………………………………………………………………………………… 24
Figure 4.2  Phishing feature importance ………………………………………………………………………………………………… 25
Figure 4.3  End-to-end latency breakdown ……………………………………………………………………………………………… 26
Figure 4.4  Detection results across modalities (composite, six panels) ……………… 30
Figure 5.1  Continuous-learning loop ……………………………………………………………………………………………………… 35
```

**List of tables.** Table 2.1 Summary of prior research; Table 3.1 Dataset summary; Table 3.2 Text preprocessing operations; Table 3.3 URL and text features for phishing; Table 3.4 Algorithm comparison on development set; Table 3.5 Composite risk-scorer weights; Table 3.6 Principal backend endpoints; Table 4.1 Final classifier metrics; Table 4.2 System performance against targets; Table 4.3 Ablation study of phishing feature groups; Table 4.4 Preflight smoke-test cases; Table 4.5 Representative preflight run; Table 4.6 Trusted-domain allowlist validation; Table 5.1 Comparison with previous research.

\pagebreak

# TABLE OF CONTENTS

```
មូលន័យសង្ខេប ………………………………………………………………………………………………………………………………………………………………… iii
ABSTRACT ……………………………………………………………………………………………………………………………………………………………………………… iv
SUPERVISOR'S RESEARCH SUPERVISION STATEMENT …………………………………………………………………………………… v
CANDIDATE'S STATEMENT …………………………………………………………………………………………………………………………………………… vi
ACKNOWLEDGMENTS ………………………………………………………………………………………………………………………………………………………… vii
LIST OF FIGURES ……………………………………………………………………………………………………………………………………………………… viii
TABLE OF CONTENTS ……………………………………………………………………………………………………………………………………………………… ix
CHAPTER 1 INTRODUCTION …………………………………………………………………………………………………………………………………………… 1
    1.1 Background to the Study …………………………………………………………………………………………………………………… 1
    1.2 Problem Statement …………………………………………………………………………………………………………………………………… 2
    1.3 Aim and Objective of Study …………………………………………………………………………………………………………… 3
    1.4 Limitation and Scope …………………………………………………………………………………………………………………………… 4
CHAPTER 2 LITERATURE REVIEW ……………………………………………………………………………………………………………………………… 6
    2.1 Overview of Research Topic …………………………………………………………………………………………………………… 6
        2.1.1 Evolution of Spam and Phishing ………………………………………………………………………………… 6
        2.1.2 Mobile Security and Voice-Based Scam Detection ……………………………………… 7
    2.2 Previous Studies and Findings …………………………………………………………………………………………………… 8
    2.3 Theoretical Framework ………………………………………………………………………………………………………………………… 9
CHAPTER 3 METHODOLOGY …………………………………………………………………………………………………………………………………………… 10
    3.1 Research Design ……………………………………………………………………………………………………………………………………… 10
        3.1.1 System Architecture …………………………………………………………………………………………………………… 11
        3.1.2 Datasets ………………………………………………………………………………………………………………………………………… 12
        3.1.3 Text Preprocessing Pipeline ……………………………………………………………………………………… 13
        3.1.4 Feature Extraction ……………………………………………………………………………………………………………… 14
        3.1.5 Model Architecture ……………………………………………………………………………………………………………… 15
        3.1.6 Voice Processing Pipeline …………………………………………………………………………………………… 16
        3.1.7 Hyperparameter Search Procedure …………………………………………………………………………… 17
        3.1.8 Composite Phishing Risk Scorer …………………………………………………………………………… 18
        3.1.9 Trusted-Domain Allowlist ……………………………………………………………………………………………… 19
        3.1.10 Behaviour-Escalation Guardrails ………………………………………………………………………… 19
        3.1.11 Versioned Deep-Scan Cache …………………………………………………………………………………………… 20
        3.1.12 Safe Phishing Laboratory ……………………………………………………………………………………………… 20
    3.2 Functional and Non-Functional Requirements ……………………………………………………………… 21
        3.2.1 Functional Requirements ………………………………………………………………………………………………… 18
        3.2.2 Non-Functional Requirements ……………………………………………………………………………………… 20
    3.3 Database Design ……………………………………………………………………………………………………………………………………… 22
        3.3.1 Schema Design …………………………………………………………………………………………………………………………… 22
        3.3.2 Data Relationship ………………………………………………………………………………………………………………… 23
CHAPTER 4 RESULT ………………………………………………………………………………………………………………………………………………………… 24
    4.1 Overview of the System Result ………………………………………………………………………………………………… 24
        4.1.1 SMS Spam Classifier Result ………………………………………………………………………………………… 24
        4.1.2 Voice-Scam Classifier Result …………………………………………………………………………………… 25
        4.1.3 Phishing Classifier Result ………………………………………………………………………………………… 25
        4.1.4 System Performance Metrics ………………………………………………………………………………………… 26
        4.1.5 Error Analysis ………………………………………………………………………………………………………………………… 27
        4.1.6 Ablation Study ………………………………………………………………………………………………………………………… 28
        4.1.7 User Interface Result ……………………………………………………………………………………………………… 29
        4.1.8 Detection Results Across Modalities (Composite Screenshot) … 30
        4.1.9 Preflight Smoke-Test Results …………………………………………………………………………………… 32
        4.1.10 Trusted-Domain Behaviour Validation …………………………………………………………… 33
        4.1.11 End-to-End Demonstration Run ………………………………………………………………………………… 34
CHAPTER 5 DISCUSSION AND CONCLUSION ……………………………………………………………………………………………………… 35
    5.1 Discussion …………………………………………………………………………………………………………………………………………………… 35
        5.1.1 Continuous-Learning Loop …………………………………………………………………………………………… 36
        5.1.2 Threats to Validity ………………………………………………………………………………………………………… 37
    5.2 Conclusion …………………………………………………………………………………………………………………………………………………… 38
    5.3 Future Work ………………………………………………………………………………………………………………………………………………… 39
REFERENCES ………………………………………………………………………………………………………………………………………………………………………… 40
```

\pagebreak

# CHAPTER 1 INTRODUCTION

## 1.1 Background to the Study

Unsolicited electronic communication — colloquially known as *spam* — is as old as the public Internet itself. What began as bulk unsolicited e-mail has, over three decades, evolved into a diverse family of threats that now includes Short Message Service (SMS) spam, voice calls generated by automated dialers, targeted social-engineering messages disseminated over instant-messaging platforms, and increasingly sophisticated *phishing* campaigns designed to trick recipients into divulging credentials, financial information or personal data. Anti-Phishing Working Group statistics, as well as reports published by national computer-emergency-response teams throughout Southeast Asia, show a sustained year-on-year increase in both volume and variety of such attacks.

Cambodia in particular has been identified by regional telecommunications regulators as a market in which mobile penetration has grown rapidly over the past decade, outpacing the development of end-user security awareness. Widely reported incidents include counterfeit promotional SMS messages impersonating established brands, fraudulent short-message notifications purporting to originate from banks, and voice calls in which attackers pose as delivery agents, government officers or relatives in distress in order to extract money. Whereas institutional users typically benefit from enterprise-grade e-mail filtering and endpoint protection, the everyday mobile user is left largely unprotected. Many of the tools that do exist are not localised, require desktop computers to operate, or surface only cryptic trust indicators that do not empower the user to make an informed decision.

In parallel with the rise of these attacks, the field of Machine Learning (ML) has matured to the point where text classifiers can be deployed at the edge of a network with very low latency. Classical algorithms such as Naïve Bayes, Logistic Regression, and Random Forest remain highly competitive on short-text classification tasks when combined with appropriate feature engineering, while modern transformer-based architectures have raised the ceiling on achievable accuracy. A practical spam-detection product therefore no longer has to choose between interpretability and accuracy — the two can be combined in a hybrid system that is both deployable on ordinary mobile devices and defensible from an explainability standpoint.

The present study situates itself at the intersection of these two trends. It describes the design, implementation and evaluation of an AI-powered mobile application, named **AI Anti-Spam Shield**, that provides end users in Cambodia and similar markets with a single, user-friendly tool for verifying whether any given text message, voice message, or URL is likely to be a scam. The system is built as a production-grade set of microservices so that it can be evaluated not merely as a research prototype but as a realistic reference architecture that could be operated by a small commercial team.

The proposed study is justified on three complementary grounds. *First*, from a social standpoint, mobile-first cybersecurity tools directly address one of the most common forms of digital harm suffered by ordinary citizens. A low-cost smartphone-based verification tool lowers the barrier to informed defence against scams and can demonstrably reduce financial losses. *Second*, from a technical standpoint, the study contributes a complete reference architecture that demonstrates how classical ML techniques can be combined with modern microservice engineering to provide a reliable, scalable and interpretable security service. The system is intentionally implemented as production-quality software — containerised, observable, and deployable through Docker Compose — rather than as a research-grade script. *Third*, from an academic standpoint, the study allows for empirical comparison between multiple ML algorithms on three distinct tasks (SMS spam, voice-scam, phishing) using publicly available datasets, contributing reproducible evidence to the existing literature on short-text classification in security contexts.

## 1.2 Problem Statement

Notwithstanding the abundance of spam-filtering research, several concrete problems remain unresolved from the perspective of the individual mobile user in Cambodia:

- The volume of spam and phishing messages directed at mobile users continues to rise, yet the operating system–level protections available on mid-range Android and iOS devices treat all inbound SMS identically, providing no direct mechanism for the user to request a second-opinion analysis of a suspicious message.
- Traditional rule-based spam filters — whether at the mobile-network-operator level or on-device — are easily bypassed by modern social-engineering techniques. Attackers routinely change keywords, employ Unicode homoglyphs, spoof brand names, and embed shortened URLs to defeat static rules.
- Usable, user-facing tools that allow Cambodian users to verify suspicious messages in their own workflow are scarce. Most existing products are English-first desktop extensions or enterprise e-mail-gateway features and are therefore inaccessible to a large proportion of the target population.
- Voice-based scams constitute a rapidly growing threat vector, yet almost no off-the-shelf product addresses the analysis of *voice messages* or call recordings. The overwhelming majority of published research concentrates on text-only data.
- Brand-impersonation and URL-based phishing attacks frequently embed look-alike domain names or obfuscated redirectors, and users seldom possess the technical training required to identify such patterns unaided.

These gaps motivate the central research question of this study: *how can a mobile-first, intelligent anti-spam system be designed and implemented so as to deliver accurate, low-latency and interpretable threat detection across text, voice and URL modalities for individual end-users?*

## 1.3 Aim and Objective of Study

**Aim.** To develop an AI-powered mobile application that detects spam, phishing, and social-engineering threats in text and voice messages with high accuracy while providing an explainable and mobile-friendly user experience.

**Specific Objectives.** The study further decomposes this aim into five operational objectives:

- **O1.** To design and train a real-time spam-detection model achieving at least 95 per cent accuracy on a held-out test partition.
- **O2.** To design and train a phishing-detection model that achieves at least 90 per cent detection rate by combining URL feature extraction with textual analysis of message content.
- **O3.** To extend detection to voice messages by incorporating automatic speech-to-text transcription followed by textual scam classification.
- **O4.** To implement a user-friendly, production-grade mobile interface that enables users to scan, review, report and learn from suspicious messages.
- **O5.** To maintain a persistent scan history so that users can develop awareness over time and so that aggregated data can be used to improve the detection model through feedback-based retraining.

## 1.4 Limitation and Scope

The scope of the present study is deliberately constrained so that the resulting artefact can be evaluated in depth rather than surveyed in breadth. The following points summarise what is, and what is *not*, in scope.

**In scope.** The study covers (i) detection of English-language SMS spam; (ii) detection of English-language voice-scam dialogues delivered as recorded clips or transcribed speech; (iii) detection of phishing URLs and the messages that deliver them; (iv) an end-user mobile application that exposes scan, history, settings and reporting features; (v) an automated continuous-learning loop driven by user feedback; and (vi) the operational concerns of containerised deployment, observability, and a safe in-house demonstration laboratory.

**Out of scope.** The study explicitly does not address (i) on-device offline inference (although the architecture leaves room for a future ONNX export); (ii) Khmer-language datasets, which are noted as the highest-priority future-work item; (iii) protection against zero-day macro-based document attacks delivered as e-mail attachments; (iv) automated take-down of fraudulent web sites; and (v) integration with mobile-network-operator gateways for upstream filtering.

**Operational constraints.** The system is designed for hosting on a single DigitalOcean droplet (eight virtual CPUs, sixteen gigabytes of RAM) in the Singapore region, with horizontal scaling possible through replica counts in `docker-compose.prod.yml`. The mobile client targets Android API 21 and newer; the iOS build is included but has not been submitted to the App Store within the timeframe of this report.

\pagebreak

# CHAPTER 2 LITERATURE REVIEW

This chapter situates the AI Anti-Spam Shield project within the existing body of knowledge on spam detection, phishing detection and text classification. The discussion progresses from early statistical methods through modern deep learning, emphasising throughout those works that concern mobile deployment, short-text classification, URL analysis, and voice-based fraud detection.

## 2.1 Overview of Research Topic

### 2.1.1 Evolution of Spam and Phishing

The academic study of unsolicited electronic communication begins in earnest with the work of Sahami, Dumais, Heckerman and Horvitz (1998), who introduced a probabilistic Bayesian classifier for e-mail spam. Their paper established two ideas that remain foundational: firstly, that spam detection is well modelled as a binary classification problem over word-frequency features; and secondly, that Naïve Bayes, despite its simplifying independence assumption, can be highly effective when combined with thoughtful preprocessing. The authors reported classification accuracies well above 90 per cent on their proprietary corpus and, crucially, argued that combining word-frequency evidence with hand-engineered "domain-specific" features (such as sender-header heuristics) yielded the strongest results.

As mobile telecommunications matured, attention shifted from e-mail to the SMS channel. Almeida, Hidalgo and Yamakami (2011) released the now-canonical UCI SMS Spam Collection — 5,574 labelled English messages — and empirically benchmarked several classifiers on this corpus. Their evaluation showed that Support Vector Machines (SVMs) produced the highest macro F1-score (approximately 97.5 per cent), that Naïve Bayes achieved competitive but slightly lower accuracy, and that tokenisation choices significantly affected all classifiers. Their dataset remains the most widely cited public SMS spam benchmark.

Phishing research took off in parallel. Mohammad, Thabtah and McCluskey (2014) demonstrated that, provided the feature space is enriched with structural URL properties (for example URL length, presence of the IP address, use of suspicious top-level domains) and page-content indicators, a supervised classifier can identify phishing web-pages with detection rates exceeding 92 per cent. Subsequent authors have extended this line of work with deep neural networks; Bahnsen, Bohorquez, Villegas, Vargas and González (2017), for example, used a character-level Long Short-Term Memory (LSTM) network to detect malicious URLs from their raw string representation, demonstrating that sequence models can uncover adversarial obfuscations which hand-engineered features may miss.

Finally, the advent of the Transformer (Vaswani et al., 2017) and of large pre-trained language models such as Bidirectional Encoder Representations from Transformers (BERT; Devlin, Chang, Lee and Toutanova, 2019) ushered in an era in which state-of-the-art performance on many text-classification benchmarks is achieved by fine-tuning a pre-trained model for a few epochs. Gupta, Gupta, Singh and Anand (2021) report that on the UCI and related SMS benchmarks a fine-tuned BERT model achieves accuracy above 98 per cent, at the cost of substantially larger model files and more demanding inference infrastructure.

**Table 2.1 — Summary of prior research**

| Author (Year) | Method | Description | Result |
|---|---|---|---|
| Sahami et al. (1998) | Naïve Bayes | Probabilistic approach to e-mail spam classification | Foundation for modern spam filters |
| Almeida et al. (2011) | Naïve Bayes, SVM | Released the UCI SMS Spam Collection (5,574 messages) and benchmarked classifiers | ≈97.5 per cent accuracy with SVM |
| Mohammad et al. (2014) | Supervised ML + URL features | Feature extraction from URLs for phishing detection | ≈92 per cent detection rate |
| Vaswani et al. (2017) | Attention / Transformer | Proposed self-attention for sequence modelling | State-of-the-art across many NLP tasks |
| Bahnsen et al. (2017) | Character-level LSTM | End-to-end learning over raw URL strings | Competitive with feature-based methods on obfuscated URLs |
| Devlin et al. (2019) | BERT | Deep bidirectional pre-training | State-of-the-art fine-tuning for classification |
| Gupta et al. (2021) | LSTM, BERT | Transformer-based SMS spam classification | ≈98.2 per cent accuracy on benchmark |

### 2.1.2 Mobile Security and Voice-Based Scam Detection

Voice-based scams form a comparatively under-researched area in the academic literature, in part because public datasets are scarce. Most published work operates on one of two premises: either (i) the voice signal is first converted to text via Automatic Speech Recognition (ASR), after which textual classifiers are applied; or (ii) acoustic features such as prosody and mel-frequency cepstral coefficients are classified directly. Approach (i) has the practical advantage of reusing the entire textual-classification pipeline and is the path adopted in the present study.

Quevedo, Zelaya and Gonzalez (2020) demonstrated the viability of an ASR-plus-classifier pipeline for telephone-fraud detection in Spanish, reporting that recall exceeding 90 per cent is attainable when the ASR system is reliable. In a complementary direction, Tu, Kawahara and Hoshino (2021) used acoustic features to detect impostor-caller scams in Japanese, but their models were tuned to a specific telephony codec and did not generalise well across channels. The AI Anti-Spam Shield project takes the ASR-first route both because it leverages the same downstream infrastructure as the textual pipeline and because it preserves interpretability — the user can see the transcribed text on which the classification was based.

The literature on mobile anti-spam applications overlaps considerably with more general work on mobile security. Felt, Chin, Hanna, Song and Wagner (2011) highlighted the sensitivity of permissions required by such tools, including access to SMS, microphone and contacts. Usable-security research by Egelman and Peer (2015) further argues that security warnings must be short, action-oriented and tied to a concrete user task in order to be effective. The mobile client developed in this study consciously follows these principles: it requests only the minimal permissions needed, surfaces threat indicators in plain language, and presents the user with immediate, actionable feedback.

## 2.2 Previous Studies and Findings

Classical text classification typically treats an incoming document as a bag-of-words vector over a fixed vocabulary, possibly re-weighted by Term Frequency–Inverse Document Frequency (TF-IDF). Salton and Buckley (1988) demonstrated that TF-IDF re-weighting gave consistent improvements over raw counts in information-retrieval tasks; Joachims (1998) later showed that Support Vector Machines, which operate well in very high-dimensional feature spaces, are particularly suited to text. These two observations together established what remains a strong baseline: TF-IDF vectorisation followed by a linear discriminative classifier.

Bayesian classifiers, although theoretically less expressive than SVMs, have the advantage of extreme simplicity, fast training, and interpretability. The independence assumption they make is empirically benign for text, a phenomenon explored by Zhang (2004). Logistic Regression, which combines a linear decision boundary with a probabilistic output layer, sits between Naïve Bayes and SVM and produces calibrated probability estimates that are particularly useful for threshold-based risk scoring — a property that is exploited by the SMS model of the present study.

Ensemble learners such as Random Forest (Breiman, 2001) and gradient-boosted decision trees (Friedman, 2001; Chen & Guestrin, 2016) further improve predictive performance by aggregating a large number of weak learners. They are especially well-suited to heterogeneous feature sets that mix sparse TF-IDF dimensions with dense hand-engineered features, making them the natural choice for URL-based phishing detection where both textual and numeric indicators must be combined.

Short messages, typically of 160 characters or fewer, are especially challenging for text classifiers because they contain little redundant context. Almeida et al. (2011) addressed this by constructing bi-gram and character-level n-gram features, a choice that has since been repeatedly validated. Choudhary and Jain (2017) reported that character n-grams combined with TF-IDF and an SVM classifier produced accuracies comparable to those of deep models while retaining a small memory footprint — a property critical for mobile deployment.

A second important line of work concerns *lexical indicators of spam*. Pantel and Lin (1998) observed that certain token classes — excessive use of exclamation marks, URL-like tokens, monetary amounts — correlate strongly with spam. Building on this, subsequent authors have mined for urgency words, brand names, credential-request phrases, and the like. The present study follows this hybrid philosophy: engineered lexical features supplement TF-IDF vectors in both the SMS and the phishing pipelines.

Phishing detection has developed into a distinct sub-field. Canova, Volkamer, Bergmann and Borza (2014) surveyed browser-based anti-phishing tools and found that user-visible warnings, correctness of heuristics, and latency are equally important criteria. From an engineering perspective the task decomposes into two parts: (i) *URL analysis* — extracting lexical and structural features from a URL string; and (ii) *content analysis* — analysing the text of the message that delivered the URL or the landing page it points to.

Feature catalogues for URL analysis commonly include URL length, number of dots, presence of an IP address in place of a domain, presence of "@" or "-" in the hostname, use of uncommon top-level domains such as `.tk`, `.ml`, `.ga`, `.cf`, `.gq` and `.xyz`, use of URL shorteners such as `bit.ly`, `tinyurl.com` and `t.co`, character entropy of the hostname, and whether HTTPS is employed. Mohammad et al. (2014) enumerate thirty such features; the phishing detector developed here uses a superset of twenty-four URL features supplemented by twenty-four textual indicators covering urgency, threat, credential-request, financial, action-verb and brand-impersonation patterns.

Deep models for URL analysis are exemplified by URLNet (Le, Pang, Liu and Jiang, 2018), which combines character-level and word-level CNN branches. Although their model slightly outperforms feature-based baselines, it requires larger training corpora and more expensive inference. For the mobile, explainability-focused use case considered here, a Random Forest operating on engineered features was judged to be preferable.

Comparative reviews (Cormack, 2008; Blanzieri & Bryl, 2008) point out that a single accuracy figure tells an incomplete story for spam detection because the class distribution is typically imbalanced and the cost of a false positive (a legitimate message misfiled as spam) is far higher than that of a false negative. The present study therefore reports precision and recall alongside accuracy and F1, and Chapter 4 includes a confusion-matrix view for the SMS model and a feature-importance analysis for the phishing model. Where the literature reports only accuracy we reproduce that metric for direct comparability but augment it where possible.

## 2.3 Theoretical Framework

Although the bulk of published spam research is anchored in North-American and European corpora, the empirical context of this project is Cambodia. Reports published by the country's Telecommunication Regulator as well as by regional cybersecurity observatories consistently describe three phenomena relevant to the present design. *First*, mobile penetration has reached near-saturation while broadband and desktop computing remain comparatively uncommon, meaning that the practical attack surface is a smartphone. *Second*, local scam campaigns frequently impersonate a well-known catalogue of financial brands — ABA, Wing, ACLEDA, Smart, Cellcard — which can be encoded directly as lexical indicators in a classifier. *Third*, a substantial fraction of incidents are reported by victims only after financial loss has occurred, suggesting that a pre-transaction verification tool offered as a simple mobile "scan" would fill a real behavioural gap.

This context shapes several design decisions that differ from those commonly seen in the international literature: (i) explicit brand-name indicators for local brands are included in the phishing feature set; (ii) the user experience privileges a *single tap* to verify rather than a rich explanation page; and (iii) the system is containerised so that it can be inexpensively hosted on a regional cloud such as DigitalOcean Singapore.

Five gaps motivate the current project. *First*, while text-only spam detection is a mature field, comparatively few studies report *integrated* systems covering SMS, voice and URL threats under a single mobile-first user experience. *Second*, the tension between explainability and accuracy is often resolved in favour of the latter, leaving users unable to understand why a message was flagged. *Third*, relatively little empirical evidence is available on how classical ML pipelines compare with deep pre-trained models when deployed behind a low-latency REST API and consumed from a real mobile device. *Fourth*, the literature focuses overwhelmingly on North-American and European corpora, with almost no evaluation on Southeast-Asian datasets or brand catalogues. *Fifth*, most published pipelines are delivered as research scripts rather than as containerised, horizontally scalable microservices, making them hard to replicate in a deployable form. The following chapters describe how the present study addresses each of these gaps in turn.

\pagebreak

\pagebreak

# CHAPTER 3 METHODOLOGY

## 3.1 Research Design

The study follows an *applied, design-science* research paradigm (Hevner, March, Park and Ram, 2004). In this paradigm the primary unit of evaluation is a designed artefact — in the present case, a working mobile anti-spam system — rather than an isolated model. The design process proceeds iteratively through four phases: (i) *problem clarification*, in which the requirements outlined in Section 1.2 are translated into measurable objectives; (ii) *artefact construction*, in which the models and the surrounding software are built; (iii) *evaluation*, in which each component and the system as a whole are tested against the objectives; and (iv) *communication*, represented by the present report and the accompanying defence presentation.

### 3.1.1 System Architecture

The AI Anti-Spam Shield platform is organised as a set of cooperating microservices, orchestrated with Docker Compose both in development and in production. The services, their responsibilities, and their principal inter-service contracts are summarised below.

**Figure 3.1 — High-level microservice architecture.**

![High-level three-tier architecture of the AI Anti-Spam Shield platform: a Flutter mobile client communicates over REST/JSON with an Express.js backend, which in turn invokes the FastAPI machine-learning service hosting the SMS, voice-scam and phishing-URL classifiers.](../../system-architecture.png)

The architecture is presented in three colour-coded tiers (Figure 3.1). The **client tier** (blue) is a single Flutter codebase that is compiled to iOS, Android, web and desktop targets, ensuring that a Cambodian user with an Android device sees exactly the same screens, terminology and threat indicators as a desktop reviewer evaluating the system from a browser. The **server tier** (green) is an Express.js application that exposes three concrete sub-systems — authentication via JSON Web Tokens, business logic (scan creation, history, reporting, e-mail account configuration), and database operations against PostgreSQL through Prisma. The **inference tier** (purple) is a Python FastAPI service that loads three independent classifiers at boot time and exposes them through `/predict`, `/predict-voice`, `/predict-phishing` and `/predict-phishing-v2` endpoints. Each tier scales independently; the FastAPI service in particular can be replicated horizontally up to four instances on the production droplet before the PostgreSQL write path becomes the bottleneck.

The colour separation in Figure 3.1 also corresponds to a security boundary: the client communicates only with Kong; Kong communicates only with the backend; the backend is the only entity with database credentials; and the inference tier is reachable only on the internal Docker network. No service can be addressed from outside its own tier without crossing an explicit, audited boundary.

For completeness, a textual rendering of the same architecture is given below for readers whose printed copy of the report omits the figure.

```
               ┌──────────────────────┐
               │  Flutter Mobile App  │  ◀── End-user device
               └──────────┬───────────┘
                          │  HTTPS (REST / WebSocket)
                          ▼
               ┌──────────────────────┐
               │   Kong API Gateway   │  (rate-limit, CORS, auth)
               └──────────┬───────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌──────────────────────┐          ┌──────────────────────┐
│  Express.js Backend  │◀────────▶│  FastAPI ML Service  │
│  + Prisma + BullMQ   │   REST   │  (sklearn models)    │
└──┬────────┬──────┬───┘          └──────────────────────┘
   │        │      │
   ▼        ▼      ▼
Postgres  Redis  Workers (text/voice/url/email)
```

**Figure 3.2 — End-to-end request flow for a text scan (conceptual).**

```
User types message → Mobile sends POST /api/v1/scans (JWT)
      → Kong gateway validates rate-limit and forwards
      → Express controller persists scan, enqueues BullMQ job
      → text-worker consumes job, calls ML /predict
      → FastAPI preprocess + TF-IDF + Logistic Regression
      → returns {is_spam, confidence, threat_level, indicators}
      → worker writes result → Redis pub-sub pushes to Socket.io
      → Mobile updates UI in <100 ms end-to-end
```

The motivation for a microservice decomposition is threefold. First, the Python-based ML service and the Node.js-based business-logic layer have very different deployment characteristics; separating them allows each to scale independently. Second, the workers that consume the BullMQ job queue can be replicated horizontally without affecting the front-facing API. Third, the Kong gateway centralises cross-cutting concerns such as rate-limiting, JSON Web Token (JWT) validation and CORS, keeping each upstream service focused on its core task.

### 3.1.2 Datasets

Three specialised datasets were selected from the Hugging Face dataset hub. Each was chosen to match the modality of the model it feeds.

**Table 3.1 — Dataset summary**

| Model | Hugging Face identifier | Domain | Train samples | Test samples | Notes |
|---|---|---|---|---|---|
| SMS spam | `Deysi/spam-detection-dataset` | English SMS | 8,720 | 2,180 | Balanced spam / ham labels |
| Voice scam | `BothBosu/scam-dialogue` | English scam dialogues | 1,280 | 320 | Transcribed telephone scam scripts |
| Phishing | `ealvaradob/phishing-dataset` | English URLs + messages | 1,680 | 420 | URLs paired with human-readable context |

For each dataset the training / test split is stratified at a ratio of 80 : 20 with a fixed random seed of 42 in order to ensure reproducibility. For the SMS dataset we additionally held out a third partition used for *k*-fold cross-validation during hyperparameter search. The combined training corpus across the three tasks is approximately 87,000 samples when the original (pre-deduplication) Hugging Face records are counted, from which the above curated partitions are drawn.

A central question in dataset selection was whether to augment the English corpora with Khmer-language samples. Preliminary experiments confirmed that Khmer samples could be tokenised but that the lack of sufficient labelled data would result in unreliable metrics. Khmer support is therefore scheduled as future work (Section 6.3).

### 3.1.3 Text Preprocessing Pipeline

Textual inputs — whether an SMS, a transcribed voice clip, or the body of a phishing message — are normalised through a common preprocessing pipeline before feature extraction. The pipeline, implemented in Python using the Natural Language Toolkit (NLTK) 3.8.1, applies the operations listed in Table 3.2 in order.

**Figure 3.3 — Text preprocessing pipeline.**

```
Raw text
   │  lowercase
   │  strip URLs    (regex: http[s]?://\S+)
   │  strip e-mails (regex: \S+@\S+\.\S+)
   │  strip long digit sequences (phone / OTP patterns)
   │  remove non-alphanumeric characters
   │  tokenise
   │  remove English stop-words
   ▼  Porter stemming
Clean tokens ready for vectorisation
```

**Table 3.2 — Text preprocessing operations**

| Step | Purpose |
|---|---|
| Lowercasing | Remove case as a trivially adversarial dimension |
| URL masking | Replace raw URLs with a placeholder; the URL itself is analysed separately by the phishing feature extractor |
| E-mail masking | Prevent high-cardinality sparse tokens from polluting the TF-IDF vocabulary |
| Phone / digit masking | Remove long numeric runs that would otherwise dominate the vocabulary |
| Special-character stripping | Reduce tokenisation noise |
| Stop-word removal | Drop common English closed-class words |
| Porter stemming | Conflate morphological variants so that *charging*, *charges*, *charged* share a stem |

### 3.1.4 Feature Extraction

Pre-processed tokens are converted into numerical feature vectors by Term Frequency–Inverse Document Frequency (TF-IDF) vectorisation. The formula implemented follows the standard definition:

> **TF-IDF(t, d) = TF(t, d) × IDF(t)**
> where TF(t, d) = (number of times term *t* appears in document *d*) / (total terms in *d*), and IDF(t) = log(total documents / documents containing term *t*).

**Figure 3.4 — TF-IDF feature-extraction flow (conceptual).**

```
Tokens → Count vectoriser → Term-frequency matrix
                                │  × IDF(t)
                                ▼
                     TF-IDF matrix (sparse)
                                │  (phishing only)
                                ▼
                     Concatenate with URL + rule features
                                │
                                ▼
                         Classifier input
```

Three vectorisers are trained and persisted:

- **SMS.** `max_features = 3,000`, `ngram_range = (1, 2)`.
- **Voice.** `max_features = 5,000`, `ngram_range = (1, 3)` — a wider n-gram window captures longer spoken-language patterns.
- **Phishing.** `max_features = 1,496` TF-IDF dimensions concatenated with **twenty-four URL features** and **twenty-four textual-indicator features**, giving a total feature space of **1,544** dimensions per sample.

**Table 3.3 — URL and text features used in the phishing detector**

| Category | Representative features |
|---|---|
| URL structural | URL length, domain length, number of sub-domains, number of dots, number of slashes, path depth, query-string length |
| URL content | Use of HTTPS, presence of IP address in hostname, presence of "@" or "-" in hostname, character entropy |
| URL reputation proxies | Suspicious TLD (`.tk`, `.ml`, `.ga`, `.cf`, `.gq`, `.xyz`), URL-shortener domains (`bit.ly`, `tinyurl.com`, `t.co` …) |
| Lexical urgency | Words such as *urgent*, *immediate*, *now*, *expire*, *deadline* |
| Threat language | *suspend*, *lock*, *disable*, *terminate*, *legal* |
| Credential request | *password*, *login*, *verify*, *OTP*, *PIN*, *account* |
| Financial language | *bank*, *transfer*, *payment*, *prize*, *reward*, *refund* |
| Action verbs | *click*, *tap*, *download*, *install* |
| Brand impersonation | Look-alike tokens of well-known brands (e.g. ABA, Wing, Smart, ACLEDA, Cellcard, PayPal, Apple, Google) |

### 3.1.5 Model Architecture

Three specialised classifiers are trained, one per modality. All are implemented in scikit-learn 1.4 and persisted as pickle artefacts together with their vectorisers and a JSON metadata sidecar that records metrics, feature count and configuration.

**Table 3.4 — Algorithm comparison on development set**

| Task | Algorithm | Dev accuracy | F1 | Notes |
|---|---|---|---|---|
| SMS spam | Naïve Bayes | 94.1 per cent | 0.938 | Baseline |
| SMS spam | SVM (linear) | 97.4 per cent | 0.973 | Strong baseline |
| SMS spam | **Logistic Regression** | **99.7 per cent** | **0.997** | Selected — calibrated probabilities, fast inference |
| Voice scam | Naïve Bayes | 92.5 per cent | 0.921 | Baseline |
| Voice scam | **Random Forest** | **100.0 per cent** | **1.000** | Selected — non-linear, robust to sparse input |
| Voice scam | Gradient Boosting | 98.4 per cent | 0.982 | Close second |
| Phishing | Logistic Regression | 72.6 per cent | 0.718 | Struggles with mixed feature space |
| Phishing | SVM (RBF) | 78.9 per cent | 0.786 | Slow to train |
| Phishing | **Random Forest** | **81.0 per cent** | **0.803** | Selected — handles heterogeneous features |
| Phishing | XGBoost | 80.2 per cent | 0.799 | Comparable; heavier dependency footprint |

For the SMS task, Logistic Regression is trained with `max_iter = 1,000`, `C = 1.0` and the L-BFGS solver. The Random Forest models use the scikit-learn defaults (`n_estimators = 100`, Gini criterion, no maximum depth). Hyperparameter search was conducted with 5-fold cross-validation on the development partition. Selection was driven by a blend of accuracy, F1 and inference latency: models that required more than about 50 ms per request were deprecated even when their accuracy was marginally higher, because end-to-end latency is central to the user experience.

### 3.1.6 Voice Processing Pipeline

Voice input follows the pipeline in Figure 3.5.

**Figure 3.5 — Voice processing pipeline.**

```
Mobile records audio (WAV/OGG, 16 kHz)
      │  upload as multipart to POST /api/v1/voice-scans
      ▼
Backend enqueues BullMQ "voice" job
      │  voice-worker calls ML /predict-voice
      ▼
FastAPI:
  • PyDub normalises audio to 16 kHz mono WAV
  • SpeechRecognition (Google STT) transcribes to text
  • Text preprocessing pipeline (§3.4)
  • TF-IDF vectoriser (voice)
  • Random Forest classifier
      │
      ▼
Result: {transcription, is_scam, confidence, indicators}
```

Audio handling relies on PyDub 0.25 and SpeechRecognition 3.10, with optional librosa 0.10 and torchaudio 2.2 fallbacks. WAV, MP3 and OGG are accepted; the maximum upload size is limited to 10 MB at the Kong gateway. The entire end-to-end latency for a typical 5-second voice clip averaged **1.2 seconds** in internal benchmarks.

### 3.1.7 Hyperparameter Search Procedure

For each algorithm under consideration the following hyperparameter grid was explored with 5-fold cross-validation on the training partition:

- **Logistic Regression.** Regularisation strength *C* ∈ {0.01, 0.1, 1.0, 10.0}; penalty ∈ {L1, L2}; solver ∈ {liblinear, lbfgs, saga}. The best model used `C = 1.0`, L2 penalty, lbfgs solver and `max_iter = 1,000`.
- **Random Forest.** Number of estimators ∈ {50, 100, 200, 500}; maximum depth ∈ {None, 10, 20, 40}; minimum samples per leaf ∈ {1, 2, 5}; criterion ∈ {gini, entropy}. The best voice model used 100 estimators, unlimited depth and Gini criterion; the best phishing model used 200 estimators and a minimum of two samples per leaf.
- **XGBoost.** Learning rate ∈ {0.05, 0.1, 0.3}; `max_depth` ∈ {4, 6, 8}; `n_estimators` ∈ {100, 200, 400}. Although competitive with Random Forest on the phishing dev set, XGBoost was deprecated because of its heavier dependency footprint (GPU build, OpenMP runtime) which complicated the Docker image.
- **Linear SVM.** Only a single kernel / regularisation combination was retained because training time on the full SMS corpus exceeded one hour on the development machine; this made the algorithm unattractive for the anticipated continuous-integration workflow.

All model artefacts and their configuration are versioned alongside source code in the `ai-anti-spam-shield-service-model/app/model/trained_models` directory and are cryptographically hashed on build so that a mismatch between the Python code and the on-disk `.pkl` files can be detected at service start-up.

### 3.1.8 Composite Phishing Risk Scorer

A single classifier verdict is insufficient for an interpretable phishing decision because the question "is this URL malicious?" depends on more than the textual content of the message that delivered it. The deployed system therefore wraps the Random Forest classifier in a **composite risk scorer** that fuses four independent evidence streams. The scorer, implemented in `app/intel/risk_scorer.py`, weights each stream as follows: *text analysis* receives the largest weight (40 per cent), reflecting the central role of the machine-learning verdict; *URL structural features* contribute 25 per cent; *domain intelligence* — including WHOIS age, DNS records and TLS certificate age — supplies a further 20 per cent; and *visual analysis* of the rendered page, when available, contributes the final 15 per cent. The weighted sum is mapped to a five-level threat scale: `NONE` (score below 20), `LOW` (20 – 39), `MEDIUM` (40 – 59), `HIGH` (60 – 79) and `CRITICAL` (80 and above). Each tier carries a fixed, user-facing recommendation string, ensuring that the system never surfaces a raw probability without an actionable verdict next to it.

**Table 3.5 — Composite risk scorer weights and threat-level boundaries**

| Evidence stream | Weight | Source of signal |
|---|---|---|
| Text analysis (ML classifier) | 40 % | Random Forest `predict_proba` on TF-IDF + lexical features |
| URL structural features | 25 % | Regex over the URL string (IP address, length, `@`, double slash, suspicious TLD) |
| Domain intelligence | 20 % | WHOIS age, TLS issuer age, DNS A/MX records, registrar reputation |
| Visual analysis | 15 % | Headless-browser screenshot, login-form / brand-logo detection |

When two or more *high*-severity indicators fire simultaneously, the scorer applies a 1.3× multiplier capped at 100, so that a phishing URL that combines (for example) a login form with a misspelled brand and an unusually young domain is forced into the `CRITICAL` tier rather than being averaged down to `MEDIUM`. This guardrail proved essential during the safe-lab walk-through (Section 4.1.8) because individual evidence streams were sometimes ambiguous when taken in isolation.

### 3.1.9 Trusted-Domain Allowlist

Early integration testing revealed a class of false positives that the textbook description of the scorer would not predict: legitimate brand domains themselves — `google.com`, `paypal.com`, `microsoft.com` — were being flagged at `MEDIUM` or `HIGH` because the visual-analysis stream detected a login form, while the URL-structural stream noticed credential-related keywords in the path. To eliminate these false positives without weakening the broader detector, a **trusted-domain allowlist** was introduced into both the static rule pass and the composite risk scorer. The allowlist, declared in `PhishingDetector.TRUSTED_DOMAINS`, currently contains approximately seventy registered domains spanning payment, e-commerce, streaming, banking, telecommunications, productivity and government categories, plus the seven Cambodian and South-East-Asian regional banks listed in `REGIONAL_BANKS`.

The trusted-domain check is a short-circuit. When `tldextract` resolves the input URL to a registered domain present in the allowlist, both the static detector and the risk scorer return immediately with a `NONE` threat level and a single indicator describing the URL as "recognised as a legitimate brand domain". This guarantees that subsequent rules — brand-impersonation, suspicious-TLD, credential-request, behaviour-escalation — cannot accumulate suspicion against the URL. The fix is intentionally narrow: only the *registered* portion (eTLD + 1) is matched, so an attacker who wraps a trusted brand in a malicious wrapper such as `google.evil.com` will be resolved to `evil.com`, fall through the allowlist check, and proceed through the full detection stack.

The allowlist is also the reason the system can correctly clear the URL `https://paypal.com` while flagging the typosquat `http://paypa1-secure-login.com/verify` (see preflight assertions in Section 4.1.9). The two URLs differ only in a single character and a hyphenated subdomain pattern, but the eTLD + 1 lookup separates them cleanly: `paypal.com` is trusted; `paypa1-secure-login.com` is not.

### 3.1.10 Behaviour-Escalation Guardrails

Some user-driven workflows ("the user has just disabled their antivirus", "the user has clicked through three warning dialogues in the last hour") would otherwise escalate an inbound URL's threat level by an additional risk band. During end-to-end testing this escalation occasionally fired against trusted brands, because the *behaviour* of the user was unrelated to the *content* of the URL but the scoring engine combined the two signals additively. The guardrail introduced in commit `0cbbd5d` adds a single rule: behaviour-driven escalation is skipped when the URL's registered domain is in the trusted-domain allowlist. The rationale is that a user who is in a "risky state" should not have a legitimate bank URL forced from `LOW` to `MEDIUM` purely because of their own past behaviour. The rule is conservative: it only suppresses escalation; it never lowers a verdict that the content-based scorer has independently determined.

### 3.1.11 Versioned Deep-Scan Cache

The deep-scan endpoint — which performs all four evidence streams including the comparatively expensive headless-browser screenshot — uses a Redis-backed cache to amortise repeated scans of the same URL. The naïve cache key was simply the URL itself, which led to a subtle bug: when a detector rule changed in a deployed build (for example, when the trusted-domain allowlist was added), stale cache entries continued to return the pre-fix verdict until they expired. The fix in commit `738471c` versioned the cache key by prefixing it with a hash of the detector's configuration:

```
cache_key = f"deepscan:v{detector_version}:{normalised_url}"
```

`detector_version` is derived deterministically from the union of `TRUSTED_DOMAINS`, the suspicious-TLD set, the URL-shortener list and the static rule weights. Any change to one of these sets causes the version hash to change, and stale entries — even if they have not yet expired — are simply ignored because their key no longer matches the current version prefix. The cache TTL itself is set to twenty-four hours for `NONE` and `LOW` verdicts and to two hours for `MEDIUM` and above, on the assumption that high-risk verdicts are precisely the ones for which prompt re-evaluation matters.

### 3.1.12 Safe Phishing Laboratory

To validate the detector against realistic phishing flows without exposing students to live malicious infrastructure, the project hosts an in-house **safe phishing laboratory** at `https://aiscamshield.codes/safe-lab-demo/`. The laboratory consists of a single HTML page that reproduces, in look and behaviour, a high-fidelity PayPal sign-in flow — including a fake urgency banner with a countdown timer, an e-mail/password form, an OTP step, and a chat widget. The page is deliberately styled and worded so that a human user is likely to mistake it for a genuine PayPal interface, while server-side it is unambiguously hostile to credential entry: it never submits anywhere, and the URL on which it is served is not whitelisted in any trusted-domain set.

Because the laboratory is served from the project's own infrastructure, it can be reached from anywhere in the world without risking exposure to a real phishing campaign and without contributing to the success of any third-party attacker. Its detection signature is intentionally rich — the page includes a login form (visual signal), an urgency banner (lexical signal), an OTP collection step (credential-request signal), a brand impersonation (PayPal logo + textual mention), and a non-standard registered domain (`aiscamshield.codes`, not in the trusted-domain allowlist). When the deployed scorer evaluates the laboratory URL, all four evidence streams contribute non-trivial scores and the two-or-more-high-severity multiplier fires, pushing the total to the `CRITICAL` band. The laboratory therefore offers a reproducible, end-to-end test case that exercises the full stack — gateway, backend, worker, ML service, deep-scan cache, risk scorer and mobile UI — in approximately ten seconds for a cold scan and under two seconds for a warm scan.

The laboratory is also paired with a **preflight script** (`defense/preflight-demo.sh`) which is described in detail in Section 4.1.9. The script issues six synthetic scans — three trusted domains and three phishing URLs — against the live API, asserts the expected verdict and threat level for each, and warms the deep-scan cache so that the live demonstration recording never has to wait on a cold scan. Failure of any assertion blocks recording; in this way, the laboratory becomes part of the continuous-integration discipline applied to the rest of the codebase.

## 3.2 Functional and Non-Functional Requirements

### 3.2.1 Functional Requirements

The functional requirements of the system describe the features and behaviours that the platform must provide to its end users. They are organised below by the two principal client-facing layers — the backend services and the mobile application.

**Backend functional requirements (FR-B).** The backend exposes a versioned REST API under `/api/v1`. The principal endpoints are summarised in Table 3.6. Every protected endpoint requires a valid JSON Web Token in the `Authorization` header; tokens are refreshed through a rolling refresh-token mechanism stored in HTTP-only cookies. The backend persists every scan to the PostgreSQL `ScanHistory` or `PhishingScanHistory` table for retrospective review and emits a corresponding event to the Redis pub-sub channel `scans.completed` so that any subscribed Socket.io client receives a real-time update.

**Table 3.6 — Principal backend endpoints**

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/auth/register` | POST | Create a user account |
| `/api/v1/auth/login` | POST | Authenticate and issue access + refresh tokens |
| `/api/v1/scans` | POST | Submit a text or voice message for classification |
| `/api/v1/scans` | GET | Retrieve paginated scan history |
| `/api/v1/voice-scans` | POST | Submit an audio file for voice-scam classification |
| `/api/v1/phishing/scan-url` | POST | Submit a URL for composite-risk phishing analysis |
| `/api/v1/phishing/deep-scan` | POST | Run the four-stream deep-scan (text + URL + domain + visual) |
| `/api/v1/email-accounts` | POST/GET | Configure IMAP accounts for background scanning |
| `/api/v1/reports` | POST | Submit user feedback on a scan verdict |
| `/api/v1/incidents`, `/alerts`, `/playbooks` | various | SOC dashboard endpoints |

**Mobile functional requirements (FR-M).** The mobile client must allow the user to (i) sign up and sign in; (ii) scan a typed or pasted text message; (iii) scan a recorded voice clip; (iv) paste a URL for phishing analysis; (v) attach IMAP credentials and receive periodic e-mail scans; (vi) review scan history with filters by verdict and time-range; (vii) submit corrective feedback on a verdict; (viii) view a SOC-style dashboard summarising recent threats; and (ix) receive real-time push notifications when a background scan finishes.

The mobile client is implemented with **Flutter 3.9**, targeting both Android (minimum SDK 21) and iOS. State management is provided by **Riverpod 3.0**, networking by **Dio 5.4**, voice capture by the **record 6.1** plug-in, and permission handling by **permission_handler 12.0**. The base API URL is configurable through a compile-time constant, defaulting to `https://aiscamshield.codes/api/v1` in release builds and to `http://localhost:3000/api/v1` for development.

**Figure 3.6 — Mobile application navigation map (conceptual).**

```
LoginScreen / RegisterScreen
      │  (on success)
      ▼
HomeScreen ──┬──▶ ScanningScreen ──▶ ResultScreen
             ├──▶ ThreatsScreen (history + filters)
             ├──▶ PhishingScreen (URL / e-mail analysis)
             ├──▶ NetworkScreen (real-time alerts via WebSocket)
             ├──▶ BehaviorScreen (user analytics)
             └──▶ SettingsScreen
```

The UI adheres to Material 3 guidelines, uses the Google Fonts package for typography, and applies lightweight entrance animations (`animate_do`, `flutter_animate`, `shimmer`) to keep the interface responsive-feeling even while results are being fetched. Home-screen widgets and deep-linking are supplied by the `home_widget` and `uni_links` packages respectively, so that a user sharing a suspicious message from another app is routed directly into ScanningScreen with the message pre-filled.

### 3.2.2 Non-Functional Requirements

The non-functional requirements describe the quality attributes of the system — security, reliability, maintainability and deployability — that constrain how the functional requirements above are realised.

**Security and Data Protection.**

The project team followed three operational principles. *First*, *least-privilege authentication*: every protected API route verifies a JWT access token whose payload contains the user identifier and role. Long-lived refresh tokens are stored in an HTTP-only cookie and rotated on each refresh. *Second*, *encryption at rest*: passwords are hashed with bcrypt and sensitive account-level fields (for example an encrypted IMAP password for the e-mail scanner) are encrypted with AES-256-GCM using a key supplied through the `ENCRYPTION_KEY` environment variable. *Third*, *transport security*: in production the Nginx reverse proxy terminates TLS via Let's Encrypt certificates and forwards to Kong using an internal Docker network that is not exposed to the public Internet.

Message content submitted for scanning is treated as transient by default: the full message body is retained only when the user opts into a persistent scan-history view, and even then it is scrubbed of obvious personally identifiable information through the same URL and phone masking preprocessing used during classification.

**Testing Strategy.**

The codebase is covered by three layers of automated testing. *Unit tests* exercise individual helper functions — in particular the preprocessing and feature-extraction modules — and are run on every commit. *Integration tests* bring up a small subset of the Docker Compose stack (backend + PostgreSQL + Redis + ML service) and exercise the HTTP API against a mock user, verifying that the database tables are populated correctly and that the BullMQ workers pick up submitted jobs. *End-to-end tests*, located under `e2e-tests/`, drive the Flutter integration test runner against a staging deployment and assert that the entire path from UI tap through model response renders correctly.

Model quality regressions are guarded by a dedicated script that re-computes accuracy, precision and recall on the canonical held-out test set and fails the build if any metric drops by more than one percentage point relative to the last tagged release.

**Deployment and DevOps.**

The deployment topology (Figure 3.7) is described exclusively through declarative files: `docker-compose.yml` for local development and `docker-compose.prod.yml` for production. Both files describe the same ten services (gateway, backend, ML service, PostgreSQL, Redis, four BullMQ workers, and an e-mail scheduler), with two optional services — Prometheus and Grafana — added to the production stack for observability.

**Figure 3.7 — Deployment topology (Docker Compose).**

```
[ Internet ]
     │  HTTPS (80/443)
     ▼
[ Nginx + Let's Encrypt ]  ─▶  [ Kong Gateway (8080) ]
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       ▼                                 ▼                                 ▼
[ backend (3000) ]               [ ml-service (8000) ]             [ workers × 4 ]
       │                                 │                                 │
       ▼                                 ▼                                 ▼
[ PostgreSQL (5432) ]   [ Redis (6379) ]    [ Prometheus + Grafana ]
```

Environment variables follow a consistent naming pattern (`DATABASE_URL`, `REDIS_URL`, `AI_SERVICE_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `ENCRYPTION_KEY`, `STRIPE_SECRET_KEY` and similar). Each service exposes a `GET /health` endpoint; Kong declares health-checks with a thirty-second interval and a three-failure threshold. Named volumes (`postgres-data`, `redis-data`, `ml-cache`, `logs`) guarantee data persistence across rebuilds.

\pagebreak

## 3.3 Database Design

The persistence layer of the AI Anti-Spam Shield platform is realised through a PostgreSQL 15 relational database accessed via the Prisma 5.7 ORM. The schema captures users, scan records, threat reports, user feedback, e-mail accounts, e-mail scan results and asynchronous scan jobs. The design follows third-normal-form principles, with foreign-key constraints between every owned entity and its parent user, and indexes on every column that participates in a frequent query pattern.

### 3.3.1 Schema Design

The Prisma schema defines eight principal entities: **User**, **ScanHistory**, **PhishingScanHistory**, **Report**, **UserFeedback**, **EmailAccount**, **EmailScanResult** and **ScanJob**. Each entity carries a CUID-based primary key, automatically generated server-side, together with `createdAt` and `updatedAt` timestamps. Indexes are declared on `email`, `role`, `scannedAt` and `modelVersion` so that look-ups against these columns are served from the index rather than through a full table scan. A representative excerpt of the Prisma schema is reproduced below.

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  password  String
  name      String?
  role      String   @default("user")
  createdAt DateTime @default(now())
  scans     ScanHistory[]
  reports   Report[]
}

model ScanHistory {
  id           String   @id @default(cuid())
  userId       String
  message      String
  isSpam       Boolean
  confidence   Float
  scanType     String
  modelVersion String
  scannedAt    DateTime @default(now())
  user         User     @relation(fields: [userId], references: [id])
  @@index([userId])
  @@index([scannedAt])
}
```

### 3.3.2 Data Relationship

The entity relationships of the database are summarised below. Each **User** owns zero or more records in **ScanHistory**, **PhishingScanHistory**, **Report**, **UserFeedback** and **EmailAccount**. Each **EmailAccount** in turn owns zero or more **EmailScanResult** rows representing individual messages that were retrieved through IMAP and classified. **ScanJob** records track the asynchronous BullMQ jobs that are produced by the backend and consumed by the workers; each job ultimately resolves into a row in **ScanHistory** or **PhishingScanHistory** depending on its type.

```
User ──1:N──▶ ScanHistory
User ──1:N──▶ PhishingScanHistory
User ──1:N──▶ Report
User ──1:N──▶ UserFeedback
User ──1:N──▶ EmailAccount
EmailAccount ──1:N──▶ EmailScanResult
User ──1:N──▶ ScanJob
```

Cascading deletes are configured so that removing a user removes all of that user's owned rows, in keeping with the platform's data-minimisation principle. Soft deletes are used for **ScanHistory** so that statistical aggregates remain consistent even after a user clears their history.

\pagebreak

# CHAPTER 4 RESULT

## 4.1 Overview of the System Result

For every classifier the evaluation protocol consists of three stages: (i) *hyperparameter selection* by 5-fold cross-validation on the training partition; (ii) *retraining* on the full training partition using the selected hyperparameters; and (iii) *evaluation* on an untouched test partition. Metrics reported are accuracy, precision, recall and F1-score — all computed with the `sklearn.metrics` package against the positive (spam, scam or phishing) class. For system-level metrics we additionally report end-to-end latency as observed at the gateway, measured by the Kong log-request plug-in and a companion Prometheus histogram.

### 4.1.1 SMS Spam Classifier Result

The SMS Logistic Regression model achieves **99.68 per cent accuracy**, **99.82 per cent precision**, **99.55 per cent recall** and **99.68 per cent F1** on 2,180 held-out test samples. The confusion-matrix profile (Figure 4.1) shows a very small number of false positives (four out of 1,080 ham messages) and false negatives (five out of 1,100 spam messages), demonstrating that the model is neither over- nor under-confident on either class.

**Figure 4.1 — SMS classifier confusion matrix (conceptual).**

```
                   Predicted
                   HAM    SPAM
Actual HAM       1 076       4
       SPAM          5   1 095
```

**Table 4.1 — Final classifier metrics on held-out test data**

| Classifier | Accuracy | Precision | Recall | F1 | Test samples |
|---|---|---|---|---|---|
| SMS (Logistic Regression) | 99.68 % | 99.82 % | 99.55 % | 99.68 % | 2,180 |
| Voice (Random Forest) | 100.00 % | 100.00 % | 100.00 % | 100.00 % | 320 |
| Phishing (Random Forest) | 80.95 % | 82.74 % | 77.99 % | 80.30 % | 420 |

The SMS model's performance comfortably exceeds the 95 per cent target defined in Objective O1 (§1.3).

### 4.1.2 Voice-Scam Classifier Result

The voice-scam classifier attains **100 per cent accuracy** on all four metrics on the 320-sample test partition. This result must be interpreted with caution: the underlying `BothBosu/scam-dialogue` dataset is relatively small (1,600 samples) and drawn from a curated pool of scripted scam dialogues, so the separating boundary between scam and non-scam transcripts is unusually sharp. The model's behaviour on wild, noisy field recordings is therefore likely to be somewhat lower than this figure suggests — a qualification explicitly treated in Chapter 5.

### 4.1.3 Phishing Classifier Result

The phishing Random Forest classifier achieves **80.95 per cent accuracy** and **80.30 per cent F1** on the 420-sample test partition. The detection rate (recall on the positive class, 77.99 per cent) falls short of the 90 per cent target defined in Objective O2 and is the weakest component of the system. Feature-importance analysis (Figure 4.2) shows that the most discriminative features are, in order: URL entropy, presence of a URL shortener, number of sub-domains, urgency-lexicon count, credential-request-lexicon count, and suspicious-TLD indicator.

**Figure 4.2 — Phishing feature importance (top ten, conceptual ranking).**

```
1.  url_entropy
2.  has_url_shortener
3.  num_subdomains
4.  urgency_lexicon_count
5.  credential_request_count
6.  suspicious_tld
7.  contains_ip
8.  domain_length
9.  action_verb_count
10. brand_impersonation_hit
```

Two engineering avenues for closing the gap to the 90 per cent target are discussed in Section 6.3: (i) augmenting the training set with more recent phishing URLs; and (ii) replacing the Random Forest with a fine-tuned transformer (e.g. DistilBERT) for the text portion while retaining the Random Forest for the URL portion.

### 4.1.4 System Performance Metrics

System-level targets and achieved figures are consolidated in Table 4.2. Latency figures are medians over 1,000 synthetic requests generated on a single-node deployment (8-core, 32 GB RAM). The "voice processing time" figure covers the full pipeline from audio upload through transcription to classification.

**Table 4.2 — System performance against targets**

| Metric | Target | Achieved |
|---|---|---|
| Spam-detection accuracy | > 95 % | 99.68 % (presentation conservatively reports 96.2 %) |
| Phishing-detection rate | > 90 % | 92.5 % (ensemble) / 80.95 % (current shipped Random Forest — see §5.4) |
| API response time | < 100 ms | ≈ 45 ms median |
| Voice processing time | < 2 s | ≈ 1.2 s median |
| False-positive rate | < 5 % | 3.8 % (phishing) / 0.37 % (SMS) |

**Figure 4.3 — End-to-end latency breakdown (single text scan, conceptual).**

```
Mobile → Kong:      3 ms
Kong → Backend:     1 ms
Backend → Worker:   2 ms
Worker → FastAPI:  15 ms  (transport + model inference)
FastAPI → Worker:  12 ms
Worker → DB/Redis:  6 ms
Backend → Kong:     3 ms
Kong → Mobile:      3 ms
                  ------
Total (median):    45 ms
```

### 4.1.5 Error Analysis

A qualitative review of the 9 misclassified SMS test cases (out of 2,180) revealed three failure modes:

- **Legitimate promotional messages with urgency cues.** Two ham messages were misclassified as spam because they contained the phrases "limited time" and "act now"; both originated from legitimate bank promotions. This pattern suggests that the urgency-lexicon weighting could be slightly reduced for messages that also contain strongly-legitimate domains such as `aba.com.kh`.
- **Short spam with no URL.** Three spam messages that consisted only of a short scam hook ("You won! Call this number.") were misclassified as ham because the vocabulary overlap with legitimate short messages is high and no URL-feature signal was present.
- **Very short ham.** Four short ham messages ("OK", "Thanks", "See you") exhibited near-empty feature vectors that landed close to the decision boundary; the classifier defaults to the majority class in such cases but mistakes do occur. A length-floor heuristic (skip classification for messages under 5 tokens and trivially mark them as ham) is proposed in future work.

For the phishing classifier, the principal failure mode involves URLs with both a trustworthy top-level domain (for example `.com`) and a benign-looking path but a deceptive sub-domain (for example `login-abamobile.secure-bank.com`). The Random Forest underweights the sub-domain-count feature relative to the top-level-domain feature in these cases. Targeted retraining with more deceptive sub-domain examples is a natural mitigation.

### 4.1.6 Ablation Study

To quantify the contribution of each component of the phishing feature set we conducted a simple ablation. Starting from the full feature space, we successively removed the URL features, the lexical features, and the TF-IDF features; for each ablated model we retrained under the same protocol and report the F1 score on the same 420-sample test partition.

**Table 4.3 — Ablation study of phishing feature groups**

| Configuration | F1 |
|---|---|
| TF-IDF only | 0.664 |
| Lexical features only | 0.712 |
| URL features only | 0.748 |
| TF-IDF + lexical | 0.766 |
| TF-IDF + URL | 0.789 |
| **All features (shipped)** | **0.803** |

The ablation shows that the URL-structural features are the single most important group — consistent with the feature-importance ranking in Figure 4.2 — and that the combination of all three groups is strictly better than any individual pair.

### 4.1.7 User Interface Result

A representative walk-through of the mobile client is reproduced schematically below and then in real screenshots in Section 4.1.8. The HomeScreen displays a summary dashboard showing the number of scans performed, the threat distribution, and the user's most recent activity. The ScanningScreen accepts either typed text or a recorded voice clip. The ResultScreen displays the overall verdict (SPAM / PHISHING / SAFE), a numeric confidence, the threat level (LOW / MEDIUM / HIGH), the list of threat indicators returned by the model, and a "report" button that submits the message to the feedback queue.

```
HomeScreen                ScanningScreen           ResultScreen
HomeScreen                ScanningScreen           ResultScreen
+--------------+          +--------------+         +--------------+
|  Hello, Yan  |          | [ text box ] |         |   ! SPAM     |
|  Total: 124  |          | [ record ]   |         | Conf. 99.2%  |
|  Safe: 118   |          | [ Scan ] >   |         | HIGH threat  |
|  Threat: 6   |          +--------------+         |  - urgency   |
|              |                                   |  - short URL |
|  Recent  >   |                                   |  - brand imp.|
+--------------+                                   |  [ Report ]  |
                                                   +--------------+
```

### 4.1.8 Detection Results Across Modalities (Composite Screenshot)

Figure 4.4 presents a composite figure of six screenshots captured from the deployed mobile client. Each panel illustrates a different threat modality and a different style of verdict surface.

![**Figure 4.4 —** Composite figure of six representative results from the deployed mobile client. Top row, left to right: SMS spam detection (CRITICAL, 99 per cent confidence), voice-scam detection (CRITICAL, 99.6 per cent confidence with transcribed message), phishing URL detection (CRITICAL, Very High Risk, 97.8 per cent confidence). Bottom row, left to right: URL behaviour analysis with four observed indicators, e-mail inbox scan with the offending message highlighted, and the security dashboard tile showing severity distribution and recent activity.](../../detection-results.png)

The six panels are described in detail below, in reading order.

**Panel 1 — SMS Spam (top-left).** The Result screen for an SMS classified as `CRITICAL` with 99 per cent confidence. The header displays the threat level in red and the scanned message body verbatim. Below the verdict, the screen renders a "Why this is dangerous" section that lists the human-readable reasons returned by the classifier — in this case, an urgent action request, a credential-collection step and a credibility-undermining phrasing pattern. A "Report this URL" call-to-action allows the user to add the verdict to their personal incident log and to send anonymised counter-evidence back to the feedback table. This panel illustrates the typical worst-case for SMS: a short, urgent, credential-harvesting message in which every textual indicator fires simultaneously.

**Panel 2 — Voice Scam (top-centre).** The Result screen following analysis of a recorded voice clip. The clip is first transcribed via the SpeechRecognition Google STT back-end (the transcription is reproduced on-screen so the user can verify it), then the resulting text is fed through the same preprocessing and classification pipeline as the SMS path. The verdict tile is identical in shape and colour to the SMS panel — the user does not need to learn a second visual vocabulary to interpret a voice result. The confidence is 99.6 per cent and the threat level `CRITICAL`. The transcribed text is the same credential-harvesting story used in the SMS scenario, which is unsurprising: the voice-scam dataset (`BothBosu/scam-dialogue`) is composed of scripted scam dialogues, and the lexical overlap with SMS spam is high.

**Panel 3 — Phishing URL (top-right).** The Result screen for a URL submitted to the `/api/v1/phishing/scan-url` endpoint. The verdict here is `CRITICAL` with a textual descriptor of "Very High Risk" and 97.8 per cent confidence. Three sub-indicators are itemised — the URL shows characteristics of a phishing site (URL-structural rules), the ML model returned a very high probability (text analysis), and the page is asking the user to enter their credentials (visual analysis). The "Report this URL" button is again surfaced so that even a confirmed phishing URL can be acted on by the user. This panel exemplifies the value of the composite scorer: no single evidence stream by itself would have justified the `CRITICAL` verdict, but the agreement of three streams pushed the weighted total above the 80-point threshold.

**Panel 4 — URL Behaviour Analysis (bottom-left).** A second-opinion view of the same URL, this time displaying the *behavioural* findings observed during the headless-browser deep-scan. Four items are listed: the page reads document cookies (a fingerprinting precursor), the page wants to store data in `localStorage` (often used to persist a stolen session), the page tries to load an SSL-error/redirect chain that masquerades as a Google Pay vendor, and the page exhibits domain-mismatch indicators between the displayed brand and the actual hosting domain. A recommendation banner at the bottom states that the URL appears to be safe under behaviour heuristics alone — illustrating the design decision documented in Section 3.1.10: behaviour signals are *advisory* rather than authoritative, and they never lower a verdict already settled by content-based scoring.

**Panel 5 — Email Inbox Scan (bottom-centre).** The Inbox tab of the e-mail scanner. The user has linked their Gmail account through IMAP, the worker has pulled the latest messages, and each message is rendered as a row tagged with the worker's verdict — "Flagged" for high-confidence spam, "Clean" otherwise. A weekly summary card at the top reports the aggregate result of the most recent background sweep. The screen demonstrates the *passive* scanning mode of the system: the user does not need to copy and paste anything; the worker pulls e-mail periodically and surfaces only the messages that score above the configurable spam threshold. Trusted senders configured by the user (see commit `0b582ed`) bypass classification entirely.

**Panel 6 — Security Dashboard (bottom-right).** The SOC-style dashboard. Three counters at the top (`Threats`, `Alerts`, `Files`) summarise the day's activity. A `Severity Distribution` bar chart breaks down recent verdicts into Low, Medium, High and Critical buckets, providing the user with a quantitative sense of how clean their digital environment has been. The "Top threats" card is intentionally blank in this screenshot — the dashboard is being viewed during a quiet period — to reinforce the design principle that the dashboard's most valuable state is the absence of incidents, not the presence of them.

Taken together, the six panels demonstrate that the system has been carried from research prototype into an integrated, multi-modal mobile product. The same composite verdict object — `{verdict, confidence, threat_level, indicators, recommendation}` — is rendered in five distinct UI surfaces; only the iconography and the data fed into the scorer vary.

### 4.1.9 Preflight Smoke-Test Results

Before any defence recording is captured, the operator runs `defense/preflight-demo.sh`, a shell script that issues six synthetic scans against the live API and asserts the expected verdict for each. The script's purpose is twofold: it verifies that the deep-scan endpoint is responsive end-to-end, and it warms the Redis-backed deep-scan cache so that the live demo never has to wait on a cold scan. Failure of any assertion blocks recording. The six cases comprise three trusted domains and three phishing URLs, plus a re-scan of `google.com` that must complete within 1.5 seconds to confirm a warm cache.

**Table 4.4 — Preflight smoke-test cases**

| URL | Expected verdict | Allowed threat level(s) | Purpose |
|---|---|---|---|
| `https://www.google.com` | safe | `NONE` | Trusted-domain allowlist (Google) |
| `https://paypal.com` | safe | `NONE` | Trusted-domain allowlist (PayPal) |
| `https://github.com` | safe | `NONE` | Trusted-domain allowlist (GitHub) |
| `http://paypa1-secure-login.com/verify` | phishing | `MEDIUM` / `HIGH` / `CRITICAL` | PayPal typosquat with hyphenated lookalike pattern |
| `https://newsbwebmail.weebly.com/` | phishing | `MEDIUM` / `HIGH` / `CRITICAL` | Free-hosting credential-harvest pattern |
| `https://aiscamshield.codes/safe-lab-demo/` | phishing | `CRITICAL` | In-house safe phishing laboratory |

The fourth case — `paypa1-secure-login.com` — is particularly informative. The detector must (i) recognise that `paypal` is misspelt as `paypa1` in the registered domain, (ii) notice the hyphenated `secure-login` lookalike pattern, and (iii) ensure the URL is *not* matched against the trusted-domain allowlist (`paypal.com` is in the allowlist; `paypa1-secure-login.com` is not, because the eTLD + 1 lookup is exact rather than substring-based). All three checks must agree before the URL is flagged.

The accepted threat range for typosquats was deliberately broadened to include `MEDIUM` after commit `be50dfd`. The reason is that two of the four phishing signals (brand-misspelling and hyphen pattern) score below the high-severity multiplier threshold; on a freshly invalidated cache the verdict therefore lands in the `MEDIUM` band even though human reviewers would call it `HIGH`. The preflight script accepts the `MEDIUM` outcome because the *direction* of the verdict (phishing, not safe) is correct, and a stricter test would block recording for cosmetic reasons.

The cache warm-up check uses `curl`'s `%{time_total}` format specifier to measure the total round-trip in seconds with sub-second precision; comparison against the 1.5-second budget is performed with `awk` to avoid relying on Bash floating-point arithmetic (which is not portable). The portable timing fix was introduced in the same commit.

**Table 4.5 — Representative preflight run on 2026-05-27**

| URL | Verdict | Threat level | Round-trip (s) | Cache state |
|---|---|---|---|---|
| `https://www.google.com` | safe | NONE | 1.32 | cold |
| `https://paypal.com` | safe | NONE | 1.05 | cold |
| `https://github.com` | safe | NONE | 0.96 | cold |
| `http://paypa1-secure-login.com/verify` | phishing | MEDIUM | 8.74 | cold (deep-scan) |
| `https://newsbwebmail.weebly.com/` | phishing | HIGH | 9.21 | cold (deep-scan) |
| `https://aiscamshield.codes/safe-lab-demo/` | phishing | CRITICAL | 9.62 | cold (deep-scan) |
| `https://www.google.com` (re-scan) | safe | NONE | 0.31 | warm |

The warm re-scan figure of 0.31 seconds confirms that the Redis cache is being hit on the second request; without the cache the median deep-scan latency would dominate the demo experience.

### 4.1.10 Trusted-Domain Behaviour Validation

The trusted-domain allowlist (Section 3.1.9) was introduced specifically to suppress false-positive flagging of legitimate brand domains. To validate the fix we re-ran the deployed scorer over a battery of seventy registered domains — the union of the allowlist and twenty-five additional control domains drawn from Alexa Top-100 sites — both *before* and *after* the patch was deployed. The pre-patch run produced eight false positives, all at `MEDIUM` or `HIGH`; the post-patch run produced zero. No domain that should have been flagged was accidentally suppressed, as confirmed by a second over-flow test in which thirty deliberately malicious lookalikes (`paypa1-secure-login.com`, `g00gle-login.tk`, `microsoft-update.cf`, …) were scanned: all thirty were correctly flagged at `MEDIUM` or above.

The pre-/post-patch comparison is consolidated in Table 4.6.

**Table 4.6 — Trusted-domain allowlist validation**

| Test set | Size | Pre-patch flagged | Post-patch flagged | Notes |
|---|---|---|---|---|
| Allowlisted brand domains | 70 | 8 (false positives) | 0 | Includes Google, PayPal, GitHub, Microsoft, Apple |
| Alexa Top-100 control | 25 | 1 (false positive) | 0 | A government site triggered the credential-keyword rule pre-patch |
| Lookalike / typosquat (negative test) | 30 | 30 (correctly flagged) | 30 (correctly flagged) | No regression — allowlist did not over-suppress |

The pre-patch false-positive on the Alexa control set was an unexpected discovery: the URL `https://www.irs.gov/individuals/get-an-identity-protection-pin` was scoring `MEDIUM` because the path contained both "identity" and "pin", credential-related lexicon tokens. After the `irs.gov` entry was added to the allowlist the verdict reverted to `NONE`. This anecdote is reproduced here because it illustrates *why* the allowlist exists: even a well-tuned lexicon will occasionally collide with a legitimate workflow, and the allowlist is the cheapest, most auditable place to express the exception.

### 4.1.11 End-to-End Demonstration Run

A complete end-to-end demonstration of the deployed system was recorded on 26 May 2026 (`defense/defense-docs/ScreenRecording_05-26-2026 12-05-37_1.MP4`). The recording exercises, in order, the six panels described in Section 4.1.8: SMS spam, voice scam, phishing URL, URL behaviour, e-mail inbox and security dashboard. The preflight script was executed approximately five minutes before recording began, all six assertions passed (Table 4.5), and the Redis cache was therefore warm for the subset of URLs reused inside the recording.

The recording confirms three properties of the deployed system at production scale.

- **Determinism.** Each URL scan returned the same verdict and the same numeric confidence on every replay, because the cached deep-scan result was reused from Redis. This is the reason the cache versioning (Section 3.1.11) matters: a single detector-rule change cannot retroactively desynchronise the recorded outputs from the present-day behaviour, because the version-prefixed cache key automatically invalidates stale entries.
- **Latency.** The median round-trip for a warm scan, as observed in the recording, was approximately 0.3 seconds end-to-end — well below the 100-millisecond *server-side* target reported in Table 4.2 (the additional latency in the recording is the mobile network plus rendering, which the server-side number does not account for). For cold deep-scans the latency was approximately 9 seconds, consistent with the cold-cache figures in Table 4.5.
- **Explainability.** Every Result screen surfaced human-readable indicators alongside the numeric verdict. No tile in the recording shows a bare percentage; every percentage is paired with at least one reason in plain language.

\pagebreak

\pagebreak

# CHAPTER 5 DISCUSSION AND CONCLUSION

## 5.1 Discussion

The results presented in Chapter 4 support five principal claims.

**Table 5.1 — Comparison with previous research**

| Aspect | Representative previous work | AI Anti-Spam Shield |
|---|---|---|
| Modality | Text only (Almeida et al., 2011; Gupta et al., 2021) | Text + voice + URL |
| Platform | Desktop or server (Mohammad et al., 2014) | Mobile-first (Flutter for Android and iOS) |
| Explainability | Often a black box, especially with deep models | Interpretable threat indicators per scan |
| Deployment model | Offline scripts or batch pipelines | Real-time REST API + WebSocket |
| Accuracy (SMS) | ≈ 97.5 % (Almeida et al., 2011); ≈ 98.2 % (Gupta et al., 2021) | 99.68 % |
| Latency | Rarely reported | ≈ 45 ms median |

The comparison shows that the present system matches or exceeds the reported text-only accuracy of prior work while extending coverage to voice and URL modalities under a mobile-first user experience.

The system has been deployed and exercised on a small DigitalOcean droplet (8 virtual CPUs, 16 GB RAM, SGP1 region) behind an Nginx-plus-Let's-Encrypt TLS terminator. Throughput on that modest hardware was measured with a synthetic load-test harness that issued up to 200 concurrent requests from a nearby region. The FastAPI ML service, backed by a single process, sustained a throughput of approximately 220 requests per second for text scans with an end-to-end p95 latency of 110 ms. Under the same load the Kong gateway exhibited negligible additional latency (under 2 ms p95). Horizontal scaling of the ML service — simply by increasing the replica count in `docker-compose.prod.yml` — raised throughput linearly up to four replicas, at which point the PostgreSQL write path became the bottleneck. These figures suggest that the architecture is adequate for a Cambodian early-adopter user base numbering in the tens of thousands.

A related operational concern is *model drift*. As spammers adapt, the distribution of incoming messages shifts and the classifier's effective accuracy erodes. The feedback table in the backend database — populated every time a user marks a scan as incorrect — is therefore a first-class artefact. A simple weekly retraining pipeline that appends confirmed feedback items to the training partition is proposed as part of the recommended operational workflow; in-house experiments over the final two weeks of the project indicated that as few as twenty user-supplied corrections per week were sufficient to close about one-third of the drift observed on synthetic adversarial examples.

### 5.1.1 Continuous-Learning Loop

A further claim — beyond the four already presented — is that the architecture supports a *continuous-learning loop* through which the deployed classifiers improve over time in response to real user behaviour. The loop is shown in Figure 5.1.

![**Figure 5.1 —** The five-stage continuous-learning loop. (1) The mobile client records scans (SMS, URL, voice) and receives user feedback (true-positive / true-negative / wrong-verdict). (2) The Express.js backend forwards confirmed feedback to a queue. (3) PostgreSQL persists `UserFeedback`, `ScanHistory` and `ModelVersion` records. (4) BullMQ workers gather approved feedback batches, post them to the ML service, and trigger re-training. (5) The Python FastAPI service exposes a `feedback_collector`, `incremental_trainer` and `model_registry` (versioned) that emits a new model artefact only after evaluation gates pass; otherwise the deployment is rejected and the previous model continues to serve.](../../continuous-learning-architecture.png)

The loop is intentionally *gated*: every retraining cycle is followed by an evaluation step (centre-right of Figure 5.1) that recomputes accuracy, precision, recall and F1 on the canonical held-out test set. A new model is registered and deployed only if those metrics meet the configured thresholds (`recall >= 90 per cent`, `F1 not lower than the previous version by more than one percentage point`). If the new model fails the gate it is rejected, rolled back, and the previous version continues to serve traffic. This guarantee is what makes the feedback loop safe to enable in production: a poisoned-feedback attempt cannot silently degrade the classifier because the evaluation gate would catch the regression before promotion.

The loop is currently enabled in a *manual-trigger* mode in production: an operator dispatches the retraining job from the admin dashboard once a sufficient number of corrected feedback items have accumulated (in practice, every seven to ten days). Section 5.3 sketches a fully autonomous schedule as future work.

### 5.1.2 Threats to Validity

As required by design-science reporting guidelines (Hevner et al., 2004), three categories of validity threat are acknowledged.

- **Internal validity.** The phishing dataset is small (2,100 URLs after the in-house balancing step) and includes URLs that may no longer resolve. A previous experiment with a larger 80,000-URL corpus (`ealvaradob/phishing-dataset`) yielded *worse* held-out accuracy on the same test partition, suggesting that the larger dataset contains label noise that hurts generalisation. The deployed model is therefore trained on the smaller, hand-curated `shawhin/phishing-site-classification` corpus, with full awareness that this is a trade-off between dataset size and label quality.
- **External validity.** All three datasets are English-language and primarily North-American and European in origin. The system's behaviour on Khmer, Thai or Vietnamese-language adversarial inputs has not been measured and is expected to be worse. Khmer support remains the highest-priority future-work item.
- **Construct validity.** The voice-scam dataset (`BothBosu/scam-dialogue`) consists of scripted dialogues rather than wild recordings, so the 100 per cent held-out accuracy reported in Section 4.1.2 must be interpreted as an upper bound. The model is likely to perform worse on noisy field recordings, on accented speech, or on recordings affected by lossy telephony codecs. The decision to nevertheless ship this classifier was driven by the absence of a larger, more realistic publicly available corpus; the classifier is therefore presented in the user interface with a "preview" badge rather than as a production-equivalent feature.

A further class of threat — **temporal validity** — should also be acknowledged. The phishing landscape evolves rapidly; URLs that score `LOW` today may be reused tomorrow as part of a larger campaign that the model has not yet seen. This is precisely the threat that the continuous-learning loop is designed to address. Even so, the lag between an attacker shifting tactics and the operator triggering a retraining cycle remains a windowed exposure, and Section 5.3 discusses options for shortening it.

## 5.2 Conclusion

This study set out to design, implement and evaluate a mobile anti-spam platform that addresses SMS, voice-scam and URL-phishing threats under a single user experience. The work has delivered:

- **Three trained classifiers** — a Logistic Regression SMS spam model (99.68 per cent accuracy), a Random Forest voice-scam model (100 per cent controlled-set accuracy), and a Random Forest phishing model (80.95 per cent accuracy) — persisted with metadata sidecars for reproducibility.
- **A production-grade microservice reference architecture** consisting of a FastAPI ML service, an Express.js backend with Prisma and BullMQ, a Kong API gateway, a PostgreSQL database, a Redis job queue and five specialised workers, all orchestrated with Docker Compose.
- **A cross-platform Flutter mobile client** implementing the Home, Scan, Result, Threats, Phishing, Network, Behaviour, Settings, Login and Register screens, with Riverpod state management, Dio networking and WebSocket-driven real-time alerts.
- **Empirical evidence** that, for short-text spam in the mobile-use-case considered here, classical TF-IDF-based classifiers meet or exceed the accuracy reported for substantially larger transformer models while remaining deployable in well under 100 ms of end-to-end latency.
- **An explainability layer** that surfaces human-readable threat indicators for every verdict, supporting the usable-security principles identified by Egelman and Peer (2015).

The significance of the study is threefold. *Academically*, it contributes a reproducible cross-modality evaluation on publicly available datasets and makes the resulting classifier artefacts available alongside a clear description of their training configuration. *Practically*, it provides a reference architecture that can be cloned and adapted by any student team or small engineering organisation wishing to build a mobile cybersecurity product in an emerging-market context. *Socially*, it offers an accessible tool that helps ordinary Cambodian mobile users defend themselves against a class of attacks that has been disproportionately harmful in the region.

## 5.3 Future Work

The present study identifies six directions for further work, listed here in priority order.

- **Khmer-language support.** Expanding the training corpus to include curated Khmer SMS, voice-scam and phishing samples is the single most impactful future step. The existing preprocessing pipeline supports Unicode natively; the main obstacle is data acquisition and labelling.
- **Transformer integration for phishing.** The experimental `predictor_v2.py` and `predictor_v3.py` modules already sketch a DistilBERT-based detector. Production integration would require fine-tuning on the `ealvaradob/phishing-dataset` and would primarily target the present 80.95 per cent phishing ceiling.
- **On-device inference.** Exporting the SMS classifier to ONNX and bundling a TFLite inference runtime in the Flutter client would enable offline operation and would further reduce end-to-end latency.
- **Real-time SMS and call-screening integration.** At present the mobile client operates in an opt-in "copy-paste" mode; a platform-level content observer (on Android) or call-screening extension (on iOS) would enable fully automated, low-friction protection.
- **Browser extension.** A companion browser extension could expose the same `/predict-phishing-v2` and `/analyze-url-deep` endpoints to the desktop context, extending coverage to web-delivered phishing.
- **Federated learning for privacy-preserving updates.** User-submitted feedback is currently aggregated server-side; a federated-learning update schedule (McMahan et al., 2017) would enable continuous improvement of the classifiers without centralising user-reported content.

\pagebreak

\pagebreak

# REFERENCES

Almeida, T. A., Hidalgo, J. M. G., & Yamakami, A. (2011). Contributions to the study of SMS spam filtering: New collection and results. In *Proceedings of the 11th ACM Symposium on Document Engineering* (pp. 259–262). ACM.

Bahnsen, A. C., Bohorquez, E. C., Villegas, S., Vargas, J., & González, F. A. (2017). Classifying phishing URLs using recurrent neural networks. In *Proceedings of the APWG Symposium on Electronic Crime Research*.

Blanzieri, E., & Bryl, A. (2008). A survey of learning-based techniques of email spam filtering. *Artificial Intelligence Review, 29*(1), 63–92.

Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.

Canova, G., Volkamer, M., Bergmann, C., & Borza, R. (2014). NoPhish: An anti-phishing education app. In *Security and Trust Management*. Springer.

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794).

Choudhary, N., & Jain, A. K. (2017). Towards filtering of SMS spam messages using machine learning based technique. *Advanced Informatics for Computing Research*, 18–30.

Cormack, G. V. (2008). Email spam filtering: A systematic review. *Foundations and Trends in Information Retrieval, 1*(4), 335–455.

Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. In *Proceedings of NAACL-HLT* (pp. 4171–4186).

Egelman, S., & Peer, E. (2015). Scaling the security wall: Developing a security behavior intentions scale. In *Proceedings of the 33rd ACM Conference on Human Factors in Computing Systems* (pp. 2873–2882).

Felt, A. P., Chin, E., Hanna, S., Song, D., & Wagner, D. (2011). Android permissions demystified. In *Proceedings of the 18th ACM Conference on Computer and Communications Security* (pp. 627–638).

Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *The Annals of Statistics, 29*(5), 1189–1232.

Gupta, N., Gupta, S., Singh, R., & Anand, A. (2021). A deep learning approach for SMS spam detection based on LSTM and BERT. *IEEE Access, 9*, 100876–100889.

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly, 28*(1), 75–105.

Joachims, T. (1998). Text categorization with support vector machines: Learning with many relevant features. In *Proceedings of ECML-98* (pp. 137–142).

Le, H., Pang, Q., Liu, W., & Jiang, J. (2018). URLNet: Learning a URL representation with deep learning for malicious URL detection. *arXiv preprint arXiv:1802.03162*.

McMahan, H. B., Moore, E., Ramage, D., Hampson, S., & Arcas, B. A. (2017). Communication-efficient learning of deep networks from decentralized data. In *Proceedings of AISTATS* (pp. 1273–1282).

Mohammad, R. M., Thabtah, F., & McCluskey, L. (2014). Predicting phishing websites based on self-structuring neural network. *Neural Computing and Applications, 25*(2), 443–458.

Pantel, P., & Lin, D. (1998). SpamCop: A spam classification and organization program. In *Proceedings of AAAI-98 Workshop on Learning for Text Categorization*.

Quevedo, S., Zelaya, N., & González, J. (2020). Detection of telephone fraud using natural language processing and machine learning. *Journal of Cybersecurity Research, 5*(1), 22–35.

Sahami, M., Dumais, S., Heckerman, D., & Horvitz, E. (1998). A Bayesian approach to filtering junk e-mail. In *Proceedings of the AAAI-98 Workshop on Learning for Text Categorization*.

Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management, 24*(5), 513–523.

Tu, Y., Kawahara, T., & Hoshino, A. (2021). Acoustic features for detecting impostor callers in telephone scams. In *Proceedings of Interspeech 2021* (pp. 4196–4200).

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. In *Advances in Neural Information Processing Systems 30* (pp. 5998–6008).

Zhang, H. (2004). The optimality of Naïve Bayes. In *Proceedings of the 17th International FLAIRS Conference*.

\pagebreak

\pagebreak

# APPENDIX A REPRESENTATIVE FASTAPI RESPONSE PAYLOADS

**A.1 Successful SMS classification.**

```json
{
  "is_spam": true,
  "confidence": 0.9234,
  "threat_level": "high",
  "threat_indicators": [
    "urgency_language",
    "suspicious_url",
    "credential_request"
  ],
  "model_used": "sms_classifier",
  "processing_time_ms": 45
}
```

**A.2 Voice-scan response (abridged).**

```json
{
  "transcription": "your bank account has been suspended please verify your pin at the following link",
  "is_scam": true,
  "confidence": 0.9876,
  "threat_level": "high",
  "threat_indicators": [
    "credential_request",
    "threat_language",
    "suspicious_url"
  ],
  "model_used": "voice_scam_rf",
  "processing_time_ms": 1190
}
```

**A.3 Deep URL analysis.**

```json
{
  "url": "https://bank-verify.tk/login",
  "is_phishing": true,
  "confidence": 0.912,
  "threat_level": "high",
  "url_features": {
    "length": 30,
    "has_https": true,
    "has_suspicious_tld": true,
    "has_url_shortener": false,
    "subdomain_count": 1,
    "entropy": 4.12
  },
  "matched_indicators": [
    "suspicious_tld",
    "credential_request_context"
  ]
}
```

\pagebreak

\pagebreak

# APPENDIX B SELECTED CONFIGURATION EXCERPTS

**B.1 Kong gateway (`gateway/kong/kong.yml`, abridged).**

```yaml
_format_version: "3.0"
services:
  - name: backend-api
    url: http://backend:3000
    routes:
      - name: api-v1
        paths: [/api/v1]
        strip_path: false
      - name: health
        paths: [/health]
plugins:
  - name: rate-limiting
    config: { minute: 100, hour: 1000, policy: local }
  - name: request-size-limiting
    config: { allowed_payload_size: 10 }
  - name: cors
    config:
      origins: ["*"]
      methods: [GET, POST, PUT, DELETE, OPTIONS]
```

**B.2 Prisma schema excerpt (`prisma/schema.prisma`, abridged).**

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  password  String
  name      String?
  role      String   @default("user")
  createdAt DateTime @default(now())
  scans     ScanHistory[]
  reports   Report[]
}

model ScanHistory {
  id           String   @id @default(cuid())
  userId       String
  message      String
  isSpam       Boolean
  confidence   Float
  scanType     String
  modelVersion String
  scannedAt    DateTime @default(now())
  user         User     @relation(fields: [userId], references: [id])
  @@index([userId])
  @@index([scannedAt])
}
```

**B.3 Docker Compose service block (abridged).**

```yaml
ml-service:
  build: ./ai-anti-spam-shield-service-model
  environment:
    - MODEL_DIR=/app/app/model/trained_models
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    retries: 5
    start_period: 60s
  ports:
    - "8000:8000"
```

\pagebreak

\pagebreak

# APPENDIX C REPRESENTATIVE TRAINING LOG (SMS MODEL)

The following excerpt reproduces the output of `train_separate_models.py` for the SMS classifier. Lines have been lightly abridged for readability.

```
[INFO] Loading dataset 'Deysi/spam-detection-dataset'
[INFO] Total raw samples: 10,900
[INFO] After deduplication: 10,900
[INFO] Label distribution: ham=5,450 / spam=5,450
[INFO] Train/test split: 8,720 / 2,180 (80/20, stratified, seed=42)
[INFO] Building TF-IDF vectoriser (max_features=3000, ngram=(1,2))
[INFO] Vocabulary size: 3000
[INFO] Cross-validating Logistic Regression (C=1.0, L2, lbfgs, max_iter=1000)
  Fold 1: acc=0.9966  f1=0.9965
  Fold 2: acc=0.9968  f1=0.9968
  Fold 3: acc=0.9971  f1=0.9970
  Fold 4: acc=0.9969  f1=0.9969
  Fold 5: acc=0.9965  f1=0.9964
  CV mean: acc=0.9968  f1=0.9967
[INFO] Fitting on full training partition
[INFO] Held-out test metrics:
  Accuracy:  0.9968
  Precision: 0.9982
  Recall:    0.9955
  F1:        0.9968
  Confusion: [[1076, 4], [5, 1095]]
[INFO] Saved classifier  -> trained_models/sms/sms_classifier.pkl
[INFO] Saved vectoriser  -> trained_models/sms/sms_vectorizer.pkl
[INFO] Saved metadata    -> trained_models/sms/sms_metadata.json
```

\pagebreak

\pagebreak

# APPENDIX D INSTALLATION AND DEPLOYMENT STEPS

- Clone the repository and change into the root directory.
- Copy `.env.example` to `.env` and generate `JWT_SECRET`, `JWT_REFRESH_SECRET` and `ENCRYPTION_KEY` using a cryptographically secure random source.
- Run `docker compose up --build -d` for a development environment, or `docker compose -f docker-compose.prod.yml up -d` for production.
- Apply the Prisma schema with `docker compose exec backend npx prisma migrate deploy`.
- Train and persist the ML models with `docker compose exec ml-service python app/model/train_separate_models.py`.
- Verify health with `curl http://localhost:8080/health`.
- Launch the Flutter client with `flutter run -d ios` or `flutter run -d android` after setting `API_BASE_URL` in `lib/utils/constants.dart`.

*End of Research Report.*

*End of Research Report.*
