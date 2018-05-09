from lib.logger import Logger
from lib.ssm import SimpleSystemsManager
log_level = 'critical'
logger = Logger(loglevel=log_level)
ssm = SimpleSystemsManager(logger)

ssm_send_command_response = {"Command": {"Comment": "EFS Backup Solution: Performs cleanup, upload logs files to S3, updates DDB and lifecycle hook. ", "Status": "Pending", "MaxErrors": "0",
                                         "Parameters": {"commands":
                                                            ['#!/bin/bash\n', '#========================================================================\n', '#\n', '# ec2 ssm script\n', '# stops fpsync process\n', '# uploads logs to S3\n', '# updates status on DynamoDB\n', '# completes lifecycle hook\n', '#\n', '#========================================================================\n', '# author: aws-solutions-builder@\n', '\n', '_az=$(curl http://169.254.169.254/latest/meta-data/placement/availability-zone/)\n', '_region=${_az::-1}\n', '_instance_id=$(curl http://169.254.169.254/latest/meta-data/instance-id)\n', '_hook_result="CONTINUE"\n', '\n', '#\n', '# uploading cloud-init and fpsync log to s3 before stopping fpsync process\n', '# parameters : [_s3bucket, _folder_label]\n', '#\n', 'echo "-- $(date -u +%FT%T) -- uploading cloud init logs"\n', 'aws s3 cp /var/log/cloud-init-output.log s3://S3_BUCKET/ec2-logs/efs-backup-backup-`date +%Y%m%d-%H%M`.log\n', 'echo "-- $(date -u +%FT%T) -- upload ec2 cloud init logs to S3, status: $?"\n', 'echo "-- $(date -u +%FT%T) -- uploading backup (fpsync) logs"\n', 'aws s3 cp /tmp/efs-backup.log s3://S3_BUCKET/efs-backup-logs/efs-backup-backup-fpsync-`date +%Y%m%d-%H%M`.log\n', 'echo "-- $(date -u +%FT%T) -- upload backup fpsync logs to S3 status: $?"\n', '\n', '#\n', '# kill fpsync process with SIGINT, wait until background processes complete\n', '# parameters : [_fpsync_pid]\n', '#\n', "_fpsync_pid=$(head -1 /tmp/efs-fpsync.log | awk '{print $4}' | awk -F '-' '{print $2}')\n", 'echo "-- $(date -u +%FT%T) -- fpsync foreground process-id: $_fpsync_pid"\n', '\n', 'sudo kill -SIGINT $_fpsync_pid\n', 'echo "-- $(date -u +%FT%T) -- kill fpsync pid status: $?"\n', '\n', 'if sudo test -e /tmp/efs-fpsync.log; then\n', '  echo "-- $(date -u +%FT%T) -- killing child rsync processes, may take up to 15 minutes"\n', '  _to1=$((SECONDS+900))\n', "  until tail -n 2 /tmp/efs-fpsync.log | grep -Po '\\d+(?=%)'\n", '  do\n', '    # timeout after 900 SECONDS\n', '    if [ $SECONDS -gt $_to1 ]; then\n', '      break\n', '    fi\n', '  done\n', "  _backup_percentage=$(tail -n 2 /tmp/efs-fpsync.log | grep -Po '\\d+(?=%)')\n", '  echo "-- $(date -u +%FT%T) -- exiting loop"\n', 'else\n', '  echo "-- $(date -u +%FT%T) -- /tmp/efs-fpsync.log file does not exist"\n', 'fi\n', '\n', '#\n', '# updating dynamo db with backup meta-data\n', '# parameters : [_nofs, _nfst, _tfs, _ttfs]\n', '#\n', "_nofs=$(cat /tmp/efs-backup.log | grep 'Number of files' | awk '{nofs += $7} END {print nofs}')\n", 'echo "-- $(date -u +%FT%T) -- Number of files: $_nofs"\n', '\n', "_nfst=$(cat /tmp/efs-backup.log | grep 'Number of files transferred' | awk '{nfst += $8} END {print nfst}')\n", 'echo "-- $(date -u +%FT%T) -- Number of files transferred: $_nfst"\n', '\n', "_tfs=$(cat /tmp/efs-backup.log | grep 'Total file size' | awk '{tfs += $7} END {print tfs}')\n", 'echo "-- $(date -u +%FT%T) -- Total file size: $_tfs"\n', '\n', "_ttfs=$(cat /tmp/efs-backup.log | grep 'Total transferred file size' | awk '{ttfs += $8} END {print ttfs}')\n", 'echo "-- $(date -u +%FT%T) -- Total transferred file size: $_ttfs"\n', '\n', '#\n', '# removing files from target efs which are not in source\n', '# parameters : [_folder_label, _interval]\n', '#\n', 'echo "rsync_delete_start:$(date -u +%FT%T)"\n', '_rsync_delete_start=$(date -u +%FT%T)\n', 'echo "-- $(date -u +%FT%T) -- sudo rsync -r --delete --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-backup-rsync.log  /backup/ /mnt/backups/efs-backup/BACKUP_INTERVAL.0/"\n', 'sudo rsync -r --delete --existing --ignore-existing --ignore-errors --log-file=/tmp/efs-backup-rsync.log  /backup/ /mnt/backups/efs-backup/BACKUP_INTERVAL.0/\n', 'echo "rsync delete status: $?"\n', 'echo "rsync_delete_stop:$(date -u +%FT%T)"\n', '_rsync_delete_stop=$(date -u +%FT%T)\n', 'echo "-- $(date -u +%FT%T) -- sudo touch /mnt/backups/efs-backup/BACKUP_INTERVAL.0/"\n', 'sudo touch /mnt/backups/efs-backup/BACKUP_INTERVAL.0/\n', '\n', '_finish_time=$(date -u +%FT%T)\n', 'echo "-- $(date -u +%FT%T) -- backup finish time: $_finish_time"\n', '\n', '#\n', '# uploading backup (rsync delete) log to s3\n', '# parameters : [_s3bucket, _folder_label]\n', '#\n', 'echo "-- $(date -u +%FT%T) -- uploading backup (rsync delete) logs"\n', 'aws s3 cp /tmp/efs-backup-rsync.log s3://S3_BUCKET/efs-backup-logs/efs-backup-backup-rsync-delete-`date +%Y%m%d-%H%M`.log\n', 'echo "-- $(date -u +%FT%T) -- upload rsync delete logs to S3 status: $?"\n', '\n', '# timestamps for (rm -rf) and (cp -al) file operations\n', "_rm_start=$(cat /var/log/cloud-init-output.log | grep 'remove_snapshot_start' | cut -d: -f2-)\n", "_rm_stop=$(cat /var/log/cloud-init-output.log | grep 'remove_snapshot_stop' | cut -d: -f2-)\n", "_hl_start=$(cat /var/log/cloud-init-output.log | grep 'create_snapshot_start' | cut -d: -f2-)\n", "_hl_stop=$(cat /var/log/cloud-init-output.log | grep 'create_snapshot_stop' | cut -d: -f2-)\n", "_err_61=$(cat /var/log/cloud-init-output.log | grep 'efs_mount_ip_not_found' | cut -d: -f4)\n", '\n', '#\n', '# getting burst credit balance from Source EFS\n', '# parameters : [_source_efs]\n', '#\n', "_mtime1=$(date --date '30 minutes ago' +%FT%T)\n", '_mtime2=$(date -u +%FT%T)\n', "_src_efs_credit_balance=$(aws cloudwatch get-metric-statistics --namespace AWS/EFS --region $_region --metric-name BurstCreditBalance --period 300 --statistics Average --dimensions Name=FileSystemId,Value=fake-efs-id --start-time $_mtime1 --end-time $_mtime2 --query Datapoints[0].['Average'] --output text)\n", 'echo "-- $(date -u +%FT%T) -- source efs BurstCreditBalance after backup: $_src_efs_credit_balance"\n', '\n', '#\n', '# update Dynamo DB Table with backup status\n', '# parameters : [_ddb_table_name, _backup_id, _backup_percentage, _region]\n', '#\n', 'if [ "$_err_61" == "efs_mount_ip_not_found" ]; then\n', '  echo "-- $(date -u +%FT%T) -- backup unsuccessful (id: B_ID)"\n', '  aws dynamodb update-item --table-name DDB_TABLE_NAME --key \'{"BackupId":{"S":"\'B_ID\'"}}\' --update-expression "SET BackupStatus = :q, BackupStopTime = :t" --expression-attribute-values \'{":q": {"S":"Unsuccessful"}, ":t": {"S":"\'$_finish_time\'"}}\' --region $_region\n', 'else\n', '  if [ "$_backup_percentage" == "100" ]; then\n', '    echo "-- $(date -u +%FT%T) -- backup completed successfully (id: B_ID)"\n', '    aws dynamodb update-item --table-name DDB_TABLE_NAME --key \'{"BackupId":{"S":"\'B_ID\'"}}\' --update-expression "SET BackupStatus = :q, NumberOfFiles = :n1, NumberOfFilesTransferred = :n2, TotalFileSize = :f1, TotalTransferredFileSize = :f2, BackupStopTime = :t, RemoveSnapshotStartTime = :rm1, RemoveSnapshotStopTime = :rm2, CreateHardlinksStartTime = :hl1, CreateHardlinksStopTime = :hl2, RsyncDeleteStartTime = :rd1, RsyncDeleteStopTime = :rd2, SourceBurstCreditBalancePostBackup = :cb1" --expression-attribute-values \'{":q": {"S":"Success"}, ":n1": {"N":"\'$_nofs\'"}, ":n2": {"N":"\'$_nfst\'"}, ":f1": {"N":"\'$_tfs\'"}, ":f2": {"N":"\'$_ttfs\'"}, ":t": {"S":"\'$_finish_time\'"}, ":rm1": {"S":"\'$_rm_start\'"}, ":rm2": {"S":"\'$_rm_stop\'"}, ":hl1": {"S":"\'$_hl_start\'"}, ":hl2": {"S":"\'$_hl_stop\'"}, ":rd1": {"S":"\'$_rsync_delete_start\'"}, ":rd2": {"S":"\'$_rsync_delete_stop\'"}, ":cb1": {"N":"\'$_src_efs_credit_balance\'"}}\' --region $_region\n', '    echo "-- $(date -u +%FT%T) -- dynamo db update status: $?"\n', '  else\n', '    echo "-- $(date -u +%FT%T) -- backup incomplete (id: B_ID)"\n', '    aws dynamodb update-item --table-name DDB_TABLE_NAME --key \'{"BackupId":{"S":"\'B_ID\'"}}\' --update-expression "SET BackupStatus = :q, NumberOfFiles = :n1, NumberOfFilesTransferred = :n2, TotalFileSize = :f1, TotalTransferredFileSize = :f2, BackupStopTime = :t, RemoveSnapshotStartTime = :rm1, RemoveSnapshotStopTime = :rm2, CreateHardlinksStartTime = :hl1, CreateHardlinksStopTime = :hl2, RsyncDeleteStartTime = :rd1, RsyncDeleteStopTime = :rd2, SourceBurstCreditBalancePostBackup = :cb1" --expression-attribute-values \'{":q": {"S":"Incomplete"}, ":n1": {"N":"\'$_nofs\'"}, ":n2": {"N":"\'$_nfst\'"}, ":f1": {"N":"\'$_tfs\'"}, ":f2": {"N":"\'$_ttfs\'"}, ":t": {"S":"\'$_finish_time\'"}, ":rm1": {"S":"\'$_rm_start\'"}, ":rm2": {"S":"\'$_rm_stop\'"}, ":hl1": {"S":"\'$_hl_start\'"}, ":hl2": {"S":"\'$_hl_stop\'"}, ":rd1": {"S":"\'$_rsync_delete_start\'"}, ":rd2": {"S":"\'$_rsync_delete_stop\'"}, ":cb1": {"N":"\'$_src_efs_credit_balance\'"}}\' --region $_region\n', '    echo "-- $(date -u +%FT%T) -- dynamo db update status: $?"\n', '  fi\n', 'fi\n', '\n', '#\n', '# update lifecycle hook with completion\n', '# parameters : [_lifecycle_hookname, _autoscaling_grp_name, _hook_result, _instance_id, _region]\n', '#\n', 'echo "-- $(date -u +%FT%T) -- updating lifecycle hook"\n', 'aws autoscaling complete-lifecycle-action --lifecycle-hook-name HOOK_NAME --auto-scaling-group-name ASG_NAME --lifecycle-action-result $_hook_result --instance-id $_instance_id --region $_region\n', 'echo "-- $(date -u +%FT%T) -- lifecycle hook update status: $?"\n']
                                                        }, "ExpiresAfter": "2017-08-15T18:59:11.748000-04:00", "ServiceRole": "", "DocumentName": "AWS-RunShellScript", "TargetCount": 1, "OutputS3BucketName": "", "NotificationConfig": {"NotificationArn": "", "NotificationEvents": [], "NotificationType": ""}, "CompletedCount": 0, "StatusDetails": "Pending", "ErrorCount": 0, "OutputS3KeyPrefix": "", "InstanceIds": ["i-05820148d33df4e76"], "MaxConcurrency": "50", "Targets": [], "RequestedDateTime": "2017-08-15T17:57:11.748000-04:00", "CommandId": "0d47c8fd-9dff-41c8-a7dd-991f551d0596"}, "ResponseMetadata": {"RetryAttempts": 0, "HTTPStatusCode": 200, "RequestId": "b0dcf461-8204-11e7-aaf7-c1d3afb664b8", "HTTPHeaders": {"x-amzn-requestid": "b0dcf461-8204-11e7-aaf7-c1d3afb664b8", "date": "Tue, 15 Aug 2017 21:57:11 GMT", "content-length": "5042", "content-type": "application/x-amz-json-1.1"}}}

replace_dict = {}
replace_dict['${_s3bucket}'] = 'S3_BUCKET'
replace_dict['${_interval}'] = 'BACKUP_INTERVAL'
replace_dict['${_ddb_table_name}'] = 'DDB_TABLE_NAME'
replace_dict['${_backup_id}'] = 'B_ID'
replace_dict['${_autoscaling_grp_name}'] = 'ASG_NAME'
replace_dict['${_lifecycle_hookname}'] = 'HOOK_NAME'
replace_dict['${_folder_label}'] = 'efs-backup'
replace_dict['${_source_efs}'] = 'fake-efs-id'

# Dynamically replace the ssm.sh script with replace_dict values
def test_ssm_create_command():
    response = ssm.create_command(replace_dict)
    for line in response:
        if '${_' in line and '{_az' not in line:
            print line
            status = 'fail'
        else:
            status = 'pass'
        logger.debug(status + ' on line >>  ' + line)
        assert status == 'pass'
    return response

def test_ssm_send_command(mocker):
    mocker.patch.object(ssm, 'send_command')
    ssm.send_command.return_value = ssm_send_command_response
    ssm.send_command('instance_id', 'AWS-RunShellScript', replace_dict)
    # Fixed Mock response
    x = ssm_send_command_response['Command']['Parameters']['commands']
    # Calling create_command function
    y = test_ssm_create_command()
    return 
    # assert x == y