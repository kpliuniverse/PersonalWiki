from diff_match_patch import diff_match_patch


def revision_dmp():
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 0
    dmp.Match_Distance = 0
    return dmp