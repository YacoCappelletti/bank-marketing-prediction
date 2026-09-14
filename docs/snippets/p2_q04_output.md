# p2_q04 - Prior-contact history

**Question:** How does prior contact history (previous outcome, contact recency, number of prior contacts) relate to the current term-deposit response rate?

**Method:** response-rate aggregation by prior-history fields.

## Response by previous outcome

| poutcome | Contacts | Subscribers | Response % |
| --- | --- | --- | --- |
| success | 1,373 | 894 | 65.11 |
| failure | 4,252 | 605 | 14.23 |
| nonexistent | 35,563 | 3,141 | 8.83 |

## Response by previously contacted (pdays != 999)

| Previously contacted | Contacts | Subscribers | Response % |
| --- | --- | --- | --- |
| False | 39,673 | 3,673 | 9.26 |
| True | 1,515 | 967 | 63.83 |

Clients with `poutcome=success` convert at **65.11%**.

![chart](../images/p2_q04_chart.png.png)
