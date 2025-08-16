# digital-archive

Going to make a way to display my huge volume of multimedia, both personal and familial. Mostly images and videos, maybe some audio.

# List of things

file-scanner.py:
- This will recursively scan a base folder, reading file metadata and (if possible) creating a thumbnail.

web-indexer.py:
- This will run every-so-often to do minor table updates based on entries in the database
- This will also do the prelimiary metadata -> values ingestion that the scanner gathers.

web/index.php:
- This is the interactive web front-end, styled with bootstrap

# Storage

Digital files will be stored in a filesystem with a common root (such as /mnt/archive). 

Metadata extracted from files will be stored in a database, currently mysql.

# Dependencies

Set to run on Python 3.12.10 with the following necessaries:

```
pip install mysql-connector-python
pip install pillow
pip install ffmpeg-python
```
# Database Schema

```
CREATE TABLE `entries` (
  `pk` bigint(20) NOT NULL,
  `hash` char(64) NOT NULL COMMENT 'sha256 hash of file',
  `filename` char(255) DEFAULT NULL COMMENT 'name of the file',
  `filepath` text DEFAULT NULL,
  `filesize` bigint(20) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'size of file in bytes',
  `filetype` char(32) DEFAULT NULL COMMENT 'mime type of file',
  `filedate` datetime DEFAULT NULL COMMENT 'date/time of file on filesystem',
  `filemetadata` mediumtext DEFAULT NULL COMMENT 'any embedded metadata in file during scan',
  `entrydate` datetime DEFAULT NULL COMMENT 'entry date/time',
  `entrygpslat` decimal(8,8) DEFAULT NULL COMMENT 'entry gps latitude',
  `entrygpslong` decimal(8,8) DEFAULT NULL COMMENT 'entry gps longitude',
  `entrygpsaltitude` bigint(20) NOT NULL DEFAULT 0 COMMENT 'entry gps altitude',
  `entryaddress` text DEFAULT NULL COMMENT 'entry address',
  `entrypeople` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT '[]' COMMENT 'json list of names in entry',
  `entrytags` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT '[]' COMMENT 'json list of tags in entry'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `people` (
  `id` int(10) UNSIGNED NOT NULL COMMENT 'primary key',
  `person` char(64) NOT NULL COMMENT 'person name',
  `qty` int(10) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'how many entries have this name'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tags` (
  `id` int(10) UNSIGNED NOT NULL COMMENT 'primary key',
  `tag` char(64) NOT NULL COMMENT 'tag',
  `qty` int(10) UNSIGNED NOT NULL DEFAULT 0 COMMENT 'how many entries have this tag'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `entries` ADD PRIMARY KEY (`pk`), ADD KEY `hash` (`hash`) USING BTREE, ADD KEY `filename` (`filename`);
ALTER TABLE `people` ADD PRIMARY KEY (`id`);
ALTER TABLE `tags` ADD PRIMARY KEY (`id`);
ALTER TABLE `entries` MODIFY `pk` bigint(20) NOT NULL AUTO_INCREMENT;
ALTER TABLE `people` MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key';
ALTER TABLE `tags` MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'primary key';
```
