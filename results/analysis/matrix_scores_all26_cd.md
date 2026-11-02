# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 26, scored: 26
* overall mean: 3.086

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Information Structure | 4 | 4 | 4.869 | 4.869 | 2312 |
| Content Quality | 5 | 5 | 4.501 | 4.501 | 2890 |
| Internationalization & Localization | 3 | 3 | 3.516 | 3.516 | 1734 |
| Format & Presentation | 4 | 4 | 2.924 | 2.924 | 2312 |
| Accessibility | 3 | 3 | 2.009 | 2.009 | 1734 |
| Usability & User Experience | 3 | 3 | 1.97 | 1.97 | 1734 |
| Maintenance & Updates | 2 | 2 | 1.03 | 1.03 | 1156 |
| Safety & Compliance | 2 | 2 | 1.013 | 1.013 | 1156 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Accessibility | Device Independence | 578 | 3.978 | 1.564 |
| Accessibility | Multi-modal Support | 578 | 1.033 | 0.251 |
| Accessibility | Accessibility Features | 578 | 1.017 | 0.165 |
| Content Quality | Consistency | 578 | 4.943 | 0.246 |
| Content Quality | Comprehensibility | 578 | 4.631 | 0.482 |
| Content Quality | Correctness | 578 | 4.529 | 0.499 |
| Content Quality | Completeness | 578 | 4.311 | 0.813 |
| Content Quality | Conciseness | 578 | 4.09 | 0.469 |
| Format & Presentation | Legibility | 578 | 4.929 | 0.257 |
| Format & Presentation | Consistent Format | 578 | 4.697 | 0.459 |
| Format & Presentation | Illustrations and Media | 578 | 1.035 | 0.261 |
| Format & Presentation | Representation of Interactive Elements | 578 | 1.035 | 0.261 |
| Information Structure | Metadata | 578 | 4.894 | 0.307 |
| Information Structure | Structured by Function | 578 | 4.867 | 0.34 |
| Information Structure | Modularity | 578 | 4.865 | 0.342 |
| Information Structure | Navigability | 578 | 4.849 | 0.358 |
| Internationalization & Localization | Cultural Neutrality | 578 | 4.919 | 0.286 |
| Internationalization & Localization | Translation-Friendly | 578 | 4.566 | 0.506 |
| Internationalization & Localization | Space Consideration | 578 | 1.062 | 0.362 |
| Maintenance & Updates | Version Control | 578 | 1.05 | 0.241 |
| Maintenance & Updates | Change Log | 578 | 1.01 | 0.131 |
| Safety & Compliance | Safety Information | 578 | 1.016 | 0.16 |
| Safety & Compliance | Legal and Copyright | 578 | 1.01 | 0.131 |
| Usability & User Experience | User-Centered Design | 578 | 3.867 | 0.504 |
| Usability & User Experience | Search and Indexing | 578 | 1.029 | 0.206 |
| Usability & User Experience | Testing and Feedback | 578 | 1.014 | 0.143 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1560 | 3.116 |
| fairseq | 1560 | 3.088 |
| flask-main | 1560 | 3.134 |
| joblib | 1560 | 3.08 |
| numpy | 1560 | 3.07 |
| openui | 1560 | 3.033 |
| pyro | 1560 | 3.06 |
| ragflow | 988 | 3.189 |
| sonnet | 1560 | 3.059 |
| torch | 1560 | 3.074 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 5694 | 2.961 |
| function | 3172 | 3.141 |
| method | 6162 | 3.174 |

