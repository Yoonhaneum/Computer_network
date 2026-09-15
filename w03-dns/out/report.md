# Task 2 Report

## Classification rule

A site is classified as third-party when the final name in its CNAME chain belongs to a different registrable domain from the original site. A CNAME that remains inside the site's own domain is not classified as third-party.

## CNAME chains and classification

| site | chain length | final zone | third party? | your rule's verdict |
|---|---:|---|---|---|
| www.microsoft.com | 2 | e13678.dscb.akamaiedge.net | yes | third-party |
| www.netflix.com | 1 | www.prod.ftl.netflix.com | no | not third-party |
| www.adobe.com | 2 | a1319.dscr.akamai.net | yes | third-party |
| www.cnn.com | 1 | cnn-tls.map.fastly.net | yes | third-party |
| www.apple.com | 3 | e6858.dsce9.akamaiedge.net | yes | third-party |
| www.korea.ac.kr | 0 | www.korea.ac.kr | no | not third-party |
| www.stanford.edu | 1 | stanford.netlifyglobalcdn.com | yes | third-party |
| www.bbc.co.uk | 2 | bbc.map.fastly.net | yes | third-party |
| www.spotify.com | 1 | atc.spotify.map.fastly.net | yes | third-party |
| www.github.com | 1 | github.com | no | not third-party |
| www.wikipedia.org | 1 | dyna.wikimedia.org | yes | third-party |
| www.nytimes.com | 3 | nytimes.map.fastly.net | yes | third-party |

## Steering result

**8 of 12 sites answered differently to a different resolver.**

The result compares the A records returned by the system, Google, and Quad9 resolvers. A difference in returned addresses shows that resolver choice affected the DNS answer, but it does not by itself prove that the resolver selected a physically nearby replica.

## Limitation of the classification rule

The classification rule uses the final CNAME's registrable domain to decide whether a site is on a third-party CDN. This is only a heuristic: a different registrable domain does not by itself prove who operates the CDN or whether the CDN is actually a third-party service.

For example, www.stanford.edu ends at `stanford.netlifyglobalcdn.com`. The rule classifies this as third-party because the final registrable domain differs from `stanford.edu`. However, the CNAME chain alone does not provide enough information to establish the ownership or exact operational relationship of that CDN. This shows why the rule should be treated as a heuristic rather than a definitive CDN ownership test.

## Resolver observations

### www.microsoft.com

- system: 23.49.206.40
- google: 23.49.206.40
- quad9: 23.0.194.92

### www.netflix.com

- system: 207.45.73.1, 207.45.72.1
- google: 207.45.72.1, 207.45.73.1
- quad9: 207.45.72.1, 207.45.73.1

### www.adobe.com

- system: 23.32.56.43, 23.32.56.11, 23.32.56.16, 23.32.56.9, 23.32.56.10, 23.32.56.34
- google: 23.67.53.170, 23.67.53.176
- quad9: 23.219.78.43, 23.219.78.44

### www.cnn.com

- system: 146.75.51.5
- google: 151.101.195.5, 151.101.67.5, 151.101.3.5, 151.101.131.5
- quad9: 151.101.131.5, 151.101.67.5, 151.101.195.5, 151.101.3.5

### www.apple.com

- system: 23.49.205.28
- google: 184.28.183.49
- quad9: 184.31.228.249

### www.korea.ac.kr

- system: 163.152.6.10
- google: 163.152.6.10
- quad9: 163.152.6.10

### www.stanford.edu

- system: 15.197.167.90, 3.33.186.135
- google: 15.197.167.90, 3.33.186.135
- quad9: 3.33.186.135, 15.197.167.90

### www.bbc.co.uk

- system: 146.75.48.81
- google: 151.101.192.81, 151.101.0.81, 151.101.128.81, 151.101.64.81
- quad9: 151.101.128.81, 151.101.192.81, 151.101.64.81, 151.101.0.81

### www.spotify.com

- system: 146.75.51.42
- google: 151.101.131.42, 151.101.3.42, 151.101.67.42, 151.101.195.42
- quad9: 151.101.195.42, 151.101.67.42, 151.101.3.42, 151.101.131.42

### www.github.com

- system: 20.200.245.247
- google: 20.200.245.247
- quad9: 20.27.177.113

### www.wikipedia.org

- system: 103.102.166.224
- google: 103.102.166.224
- quad9: 103.102.166.224

### www.nytimes.com

- system: 146.75.49.164
- google: 151.101.1.164, 151.101.65.164, 151.101.129.164, 151.101.193.164
- quad9: 151.101.65.164, 151.101.129.164, 151.101.193.164, 151.101.1.164

