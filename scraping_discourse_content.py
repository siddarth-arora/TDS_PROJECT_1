#TDS Discourse posts with content from 1 Jan 2025 - 14 Apr 2025.

import json
import requests 

from datetime import datetime, timezone

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34?page="
HEADERS = {
    "Accept": "application/json",
    "cookie": "_fbp=fb.2.1685009617749.827372375; _ga_MXPR4XHYG9=GS1.1.1727465592.1.1.1727465621.0.0.0; _ga_WMF1LS64VT=GS1.1.1727465574.2.1.1727465635.0.0.0; _ga_K38CF65X4M=GS1.1.1739974908.1.0.1739974916.0.0.0; _gcl_au=1.1.713156231.1745229867; _gcl_gs=2.1.k1$i1748155813$u129582030; _gcl_aw=GCL.1748155816.CjwKCAjw3MXBBhAzEiwA0vLXQXCHOMchU5lOVP3nP-F4471Qtge6l3J_kUMy242aCkL6Q60sgYG6XBoCF1oQAvD_BwE; _ga_5HTJMW67XK=GS2.1.s1748695194$o238$g0$t1748695241$j13$l0$h0; _ga_QHXRKWW9HH=GS2.3.s1749753644$o42$g0$t1749753644$j60$l0$h0; _ga=GA1.1.19740650.1685009618; _ga_08NPRH5L4M=GS2.1.s1749753675$o572$g1$t1749755572$j51$l0$h0; _t=qIMs1jVy3%2BmlFoKMNHX4LfTR6q8%2FHTw0EDi1%2BmEy8FRCKsSQQzCgQ%2F0lf5bxxHmIDm5SY5guvfeaUtujZMomquniU9QEO%2FygYqkmxmokvCgLsP%2F7ebgMUGgj4VJeR3eZd5LmVLwFhYvYX98%2FsQPZdbysmuWtj0%2FDCBGkRLGTlCJOIygJ6X5w9N5JfaAcBRB%2FW03Dxjchsje5lh%2BVRvCB%2F%2BM9Ey8RasfS4v765YFOLUtuynEbUoMQfzQllmhR7sJnpsbeIGgtCtQt0GvmTN8QDfD%2B%2BPbEOysgZBVunu0L%2BoNtJ4T8Y8ZhJuAaMD2CIXpUajEmTg61Ug0%3D--GihAz%2FJbodu9fm5j--lhFXUQxSMa319pBKxl6K0w%3D%3D; _forum_session=S%2F7ja4jwhSm05sQSXZ3p08PYifswK088wOxZQcJOiJ5INBw3%2BU8RrTEHE7BnaXyntjDzKD4a%2FPKYeU7SFUd2pLcQbSfG6nspsBsmDdbCvbGaijVMxT8DWvVNvf5yojfE%2B3UCMLO9hTqSJzwPeOuDdsL1jgoyn9EXjEqhsc4Ll0GkrTjVFoIMMxDgoWRJslNs8XUqYVkTh9bTqnS6Qceywy3G6w3FenFmoVG9uaitNzuqRSXzG2M5r5PGVRZ3JqW01RSM6vXb%2FEOXE0%2Bf%2Fnm6hlG3010U3rRz7LCrvCyTtd4B1YMwRajcz9mmxR7E9geWnVikaK2hz7E9HoAQSpkW7VzVzG6E%2FDj9KV52ecICaMsfAmXxQ23RwBoGnl2bRFPJRZN6sT6yEOLdVX3mSQFmim98APEyZg%3D%3D--XO2cFoeZfQHc9um4--jQdkmR6EdAPmgq%2FggtQx7g%3D%3D"
}

START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 4, 14, tzinfo=timezone.utc)
PAGE = 1
all_posts = []

while True:
    response = requests.get(BASE_URL + str(PAGE), headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed on page {PAGE}")
        break
    
    data = response.json()
    topics = data.get("topic_list", {}).get("topics", [])

    if not topics:
        break

    for topic in topics:
        created_at_str = topic.get("created_at")
        if created_at_str:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))

            if START_DATE <= created_at <= END_DATE:
                all_posts.append({
                    "id": topic["id"],
                    "title": topic["title"],
                    "created_at": created_at_str,
                    "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{topic['slug']}/{topic['id']}"
                })
            elif created_at > END_DATE:
                # Stop if topics are already newer than target window
                continue

    # If no more pages exist
    if "more_topics_url" not in data.get("topic_list", {}):
        break
    
    print(PAGE)
    PAGE += 1

print(len(all_posts), "posts found.")
with open("tds_posts_jan_to_apr_2025.json", "w") as f:
    json.dump(all_posts, f, indent=4)

