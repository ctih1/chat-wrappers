import os
KEY = os.environ["YOUTUBE_API_KEY"]

while True:
    import requests

    from typing import Literal, TypedDict, List
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import time

    temp_ids: set = set()

    class AuthorChannelId(TypedDict):
        value: str

    class CommentSnippet(TypedDict):
        channelId: str
        videoId: str
        textDisplay: str
        textOriginal: str
        authorDisplayName: str
        authorProfileImageUrl: str
        authorChannelUrl: str
        authorChannelId: AuthorChannelId
        canRate: bool
        viewerRating: Literal["none"]
        likeCount: int
        publishedAt: str
        updatedAt: str

    class ReplyCommentSnippet(CommentSnippet):
        parentId: str

    class Comment(TypedDict):
        kind: Literal["youtube#comment"]
        etag: str
        id: str
        snippet: CommentSnippet

    class ReplyComment(TypedDict):
        kind: Literal["youtube#comment"]
        etag: str
        id: str
        snippet: ReplyCommentSnippet

    class Replies(TypedDict):
        comments: list[ReplyComment]

    class ThreadSnippet(TypedDict):
        channelId: str
        videoId: str
        topLevelComment: Comment
        canReply: bool
        totalReplyCount: int
        isPublic: bool

    class CommentThread(TypedDict):
        kind: Literal["youtube#commentThread"]
        etag: str
        id: str
        snippet: ThreadSnippet
        replies: Replies | None

    class PageInfo(TypedDict):
        totalResults: int
        resultsPerPage: int

    class CommentThreadListResponse(TypedDict):
        kind: Literal["youtube#commentThreadListResponse"]
        etag: str
        pageInfo: PageInfo
        items: List[CommentThread]

    creds = Credentials.from_authorized_user_file(
        "token.json",
        ["https://www.googleapis.com/auth/youtube.force-ssl"],
    )

    while True:
        print("Check loop activated")
        res = requests.get(
            "https://www.googleapis.com/youtube/v3/commentThreads",
            params={
                "part": "snippet,replies",
                "maxResults": 100,
                "videoId": "UE_23gIClQs",
                "key": KEY,
            },
        )

        comments: CommentThreadListResponse = res.json()
        import json

        for comment in comments["items"]:
            replies = comment.get("replies")
            is_handled = False

            if replies is not None:
                for reply in replies["comments"]:
                    snip = reply["snippet"]
                    if snip["authorChannelId"]["value"] != "UCKwb5Ik_RNhc8qDvmsMsNBg":
                        print("Not correct user")
                        continue
                    else:
                        is_handled = True
                        print("Comment already handled")
                        break

            if comment["id"] in temp_ids:
                print("Already handled temp")
                is_handled = True

            if is_handled:
                continue

            res = requests.post(
                "http://192.168.32.88:3001/api/chat",
                json={
                    "source": "youtube",
                    "ip": comment["snippet"]["channelId"],
                    "text": comment["snippet"]["topLevelComment"]["snippet"][
                        "textOriginal"
                    ],
                },
            )

            if res.status_code == 200:
                text = "published"
                temp_ids.add(comment["id"])
            else:
                try:
                    print(res)
                    text = res.json()["message"]
                except Exception as e:

                    print(e)
                    text = "API call failed"

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            yt = build("youtube", "v3", credentials=creds)
            req = yt.comments().insert(
                part="snippet",
                body={"snippet": {"parentId": comment["id"], "textOriginal": text}},
            )

            res = req.execute()
            print(res)

        time.sleep(25)

    print("restarting")
    time.sleep(10)
