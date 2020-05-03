# Zerotier Terraform DNS

This container scrapes the Zerotier API for hosts, their names, and corresponding IP addresses.

It then constructs a terraform template that matches the cloudflare terraform spec and adds it to a file in a repository and pushes the repository.

I send a webhook to it whenever my private network repository gets updated with new hosts defined in their own terraform config or something else. This pushes to a seperate repository private that is applied via terraform cloud. 

I've deployed in kubernetes, if you would like any pointers, contact me on keybase or matrix.

## Expected variables

```yaml
ssh_key: Add this to your repo's deploy keys and give it write access.
webhook_secret: This secret will be part of the url, https://example.com/hook/webhook_secret 
git_url: Your repository url, expects ssh git url.
network_id: Your zerotier network id.
```

## Ignore

If the phrase `dns-ignore` appears in the description of any node, it will be ignored.
If the name of the node is empty, it will be ignored.

## Build

```bash
docker build -t aditsachde/zerotier-cf-webhook:11 -f Dockerfile .
docker push aditsachde/zerotier-cf-webhook:11                    
```