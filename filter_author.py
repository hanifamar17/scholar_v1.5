def filter_by_author(response):
    # Cari elemen dengan class "author"
    author = response.css(".author::text")

    # Jika elemen tersebut berisi "Nurochman"
    if author[0].strip() == "Nurochman":
        # Cari elemen dengan class "gs_a_cit"
        institution = response.css(".gs_a_cit::text")

        # Jika elemen tersebut berisi "informatika uin sunan kalijaga"
        if institution[0].strip() == "informatika uin sunan kalijaga":
            return True

    return False