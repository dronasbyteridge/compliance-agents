from app.services.compliance_runner import run_compliance_assist


async def cms_upload_event(document_text: str):
    """
    Triggered when new legislative document is uploaded.
    """

    print("New CMS Document Uploaded")

    result = await run_compliance_assist(document_text)

    return result
