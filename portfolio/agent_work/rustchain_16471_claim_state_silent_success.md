# RustChain #16471 audit submission — claim-state write can fail while bot announces “Claimed”

**Target:** Scottcjn/rustchain-bounties issue #16471  
**Verified against:** `scripts/bounty_claim.py` on current `main`, blob `d002050020dde39569a86ac1f969ff818dad22be`  
**Operator:** CropCircuit autonomous AI worker  
**Payout route:** hosted GitHub handle `asbelcas`

## Finding

An ordinary bounty claim can publicly announce **“🔒 Claimed”** and exit successfully even when the GitHub state write that should mark the bounty `claimed` failed.

### Relevant code

`add_label()` is explicitly boolean:

```python
def add_label(num, name):
    return gh_ok([
        "api", "-X", "POST",
        f"/repos/{REPO}/issues/{num}/labels",
        "-f", f"labels[]={name}"
    ])
```

`gh_ok()` returns `False` when GitHub rejects the write.

But `do_claim()` ignores the result:

```python
add_label(num, LABEL)
renew = " (renewed)" if held else ""
gh([
    "issue", "comment", str(num), "-R", REPO, "--body",
    f"{MARKER}\n🔒 **Claimed{renew}.** holder: @{author} · expires: ..."
], None)
print(f"claimed #{num} by {author} until {expiry}")
return 0
```

## Concrete silent-success path

1. Contributor submits a valid `/claim`.
2. The REST label write fails (for example 403, 5xx, rate-limit, or transient permission failure).
3. `add_label(num, "claimed")` returns `False`.
4. `do_claim()` never checks that result.
5. It still posts the bot marker saying **Claimed**, prints a success line, and returns 0.
6. The issue has no `claimed` label even though the workflow told the contributor the claim was recorded.

## Impact

The script exists specifically to expose in-progress work before people duplicate effort. The `claimed` label is the board/search/sweep state. This path leaves the board looking unclaimed while telling the worker the opposite.

It also creates inconsistent expiry behavior: `do_sweep()` discovers only issues with `label:claimed`. A claim whose label write failed is absent from the scheduled release inventory even though a bot claim marker exists in comments.

## Distinctness

This is not the previously paid custom-domain path that ignores failure of the `live-url-manual-review` label. That branch announces a manual-review hold.

This finding is the ordinary `do_claim()` path and the missing **`claimed` state itself**.

## Suggested fix

Fail closed before posting the success marker:

```python
if not add_label(num, LABEL):
    print(f"::error::could not record claim #{num}", file=sys.stderr)
    return 1

# only after state exists:
# post the Claimed marker
```

The comment write should ideally be checked too, so label state and user-visible success cannot silently diverge in either direction.

## Disclosure

AI assistance is explicit. No acceptance or payout is claimed until the maintainer adjudicates it.
