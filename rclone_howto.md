Brian Blaylock  
October 10, 2018

# How to use `rclone` to access GOES16 and NEXRAD on Amazon AWS

As part of NOAA's Big Data Project, Amazon makes available NEXRAD, GOES16, and other data publicly available via their Amazon Web Services. You can use `rclone` to access this data and download for your use.

## 1. Download and install `rclone` on your linux machine

https://rclone.org/

## 2. Configure `rclone` to access Amazon S3
After `rclone` has been downloaded and installed, configure a remote by typing `rclone config`. Then type `n` for `new remote`.

Name the remote anything you like, but use a name that you remind you it accesses the public Amazon S3 buckets. I named mine `publicAWS`. 

Set _Type of Storage_ as option 3 `Amazon S3 Compliant Storage Providers`

Set _Storage Provider_ as option 1 `Amazon Web Services S3`

Leave everything else blank (push enter).

The prompt will ask you if the following is correct:

    [publicAWS]
    type = s3
    provider = AWS
    env_auth =
    access_key_id =
    secret_access_key =
    region =
    endpoint =
    location_constraint =
    acl =
    server_side_encryption =
    storage_class =

Exit the setup.

## 3. `rclone` access to public buckets
You will use the remote you just set up to access NOAA's public buckets on Amazon Web Services S3. Below are the names of some of NOAA's public buckets.

|Data| Bucket Name| Documentation |
|--|--|--|
|GOES16| `noaa-goes16`| [link](https://registry.opendata.aws/noaa-goes/) |
|NEXRAD| `noaa-nexrad-level2`| [link](https://registry.opendata.aws/noaa-nexrad/) |

### List directories

    rclone lsd publicAWS:noaa-goes16/

### Copy file or files to your local machine

    rclone copy publicAWS:noaa-goes16/ABI-L2-MCMIPC/2018/283/00/OR_ABI-L2-MCMIPC-M3_G16_s20182830057203_e20182830059576_c20182830100076.nc ./


