-- MySQL dump 10.13  Distrib 5.7.24, for Linux (x86_64)
--
-- Host: 159.89.167.64    Database: AutographaMTStaging
-- ------------------------------------------------------
-- Server version	5.7.25-0ubuntu0.16.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Users`
--

DROP TABLE IF EXISTS `Users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Users` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Fname` text COLLATE utf8_bin NOT NULL,
  `Lname` text COLLATE utf8_bin NOT NULL,
  `Email` varchar(50) COLLATE utf8_bin NOT NULL,
  `Email_verified` tinyint(1) DEFAULT '0',
  `Verification_code` text COLLATE utf8_bin NOT NULL,
  `Password_salt` blob NOT NULL,
  `Password_hash` blob NOT NULL,
  `Role_id` int(11) NOT NULL DEFAULT '1',
  `Organisation_id` int(11) NOT NULL DEFAULT '1',
  `Token` varchar(200) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`ID`),
  KEY `Role_id` (`Role_id`),
  KEY `Organisation_id` (`Organisation_id`),
  CONSTRAINT `Users_ibfk_1` FOREIGN KEY (`Role_id`) REFERENCES `Roles` (`ID`),
  CONSTRAINT `Users_ibfk_2` FOREIGN KEY (`Organisation_id`) REFERENCES `Organisations` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Users`
--

LOCK TABLES `Users` WRITE;
/*!40000 ALTER TABLE `Users` DISABLE KEYS */;
INSERT INTO `Users` VALUES (1,'Bijo','Babu','bijob89@gmail.com',1,'1af35daae9a44eb9b4307f7bad7a499a',_binary '59db40f4ac0242418b2fde48f28892fd',_binary 'ûı†æ∑-¡ym\≈RZô†ü±∂ç\"/uôﬂ®b¸EMtRì∑πöé	ÛY\ zSLR\r\",ü\ƒ#≠zSmñ?ıñ',3,1,'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJiaWpvYjg5QGdtYWlsLmNvbSIsImZpcnN0TmFtZSI6IkJpam8iLCJyb2xlIjozLCJleHAiOjE1NTAwNTExOTN9.kWi_bSOfioiNFU_HN_jaz8hCNq6PkXE4l_CFY87ojkY'),(2,'Bijo','Babu','bijo.babu@bridgeconn.com',1,'635462',_binary '689e070408b64a40a53fb843aa19bd14',_binary 'kÒÄ+\–\'~Ç\ËIkëíL,\»˘Y\ÈéU7xz\œ|\ÿ\‚Ù^ç\Â\n\Ë¡\·ãZ`Wi\Í\›\'°x[vl\Óªbã∂ï',2,2,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoyLCJmaXJzdE5hbWUiOiJCaWpvIiwiZXhwIjoxNTQyODg0NDYxLCJzdWIiOiJiaWpvLmJhYnVAYnJpZGdlY29ubi5jb20ifQ.OTO5vGEyTDwjtIKFajf_4iJJsd-P3-1cqDmUHTaafMk'),(3,'Auto','test','AutoMTTest@yopmail.com',1,'5b2c05087fa844419bf9ebd6f95222b1',_binary 'e516b759cd2640bb924b59f153c8636f',_binary 'É\·X≥¯§°O\Œ\'y®ïl{gZû\Î\’ ûú<¨üQ\«\….\‹1]õÅXII\0H¢cº\·ï\Z~ª#£\‘¬òê',2,3,NULL),(4,'y23','last','y23@yopmail.com',1,'655768',_binary '8149cf6143154bbc92da3a40978825d2',_binary 'Ñ7õö\'9ôv\‰5˝BÛaçYhÚ\ÿNµK\ƒ>Ωè0ØpcøqH\ÔÛA¨{2Û*Qx\Ê\‰W\‚7\r:\r\ÎM',1,1,'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmaXJzdE5hbWUiOiJ5MjMiLCJzdWIiOiJ5MjNAeW9wbWFpbC5jb20iLCJyb2xlIjoxLCJleHAiOjE1NTAwNDkyNjR9.n1kYORb43xMD6Jrx-TSInz9akLBobeoEQDeZPnBCCDo'),(5,'Ftest','Ltest','test@test',1,'8593f4d0e9304be89ad5072abc026b1c',_binary 'ba3acbd8966a46fcaf931448b74f7edc',_binary 'Cm•«µÚXy-E`\ŒZ∫Ë§¶≠\⁄\Î«≤CsaY==˙Qî7{éj\ \Ó\Ár=$x®á˛Éí˝R∞\ÕPï8P_\È',1,1,'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QHRlc3QiLCJyb2xlIjoxLCJmaXJzdE5hbWUiOiJGdGVzdCIsImV4cCI6MTU1MDA0MjcyNX0.E0B9qh0rH5BcljXiPilhuMVwiNit5_PCLudKf7EInVE'),(6,'bcsauto','user','bcsautouser@yopmail.com',0,'ca5b5a1c7f6d42c584ce76c02a36fd76',_binary '0b1410fac68648b7813f860d2fbecab5',_binary '˚g7π\—L€öyæ\⁄a\∆Zv\ ~oäu≥Ü:%\ÿv\…rg\”\ÍÄ\Î_º\›YB\’s+D\Œ\‘~\0≠\›ÒﬂçÄ˛Uππ\…',1,1,NULL),(7,'bcsauto','user','bcsautouser1@yopmail.com',0,'f6bb9ebedf05408badd67be60dfdf0e5',_binary 'a2346ed358ec495fa83d60c67bfaf765',_binary 'hO˛˝gH^?l\È\‚ø	\·.fäjÑüìˆ˙û∏\‚SLˆ\\Æèk6 \¬\‚\–0\n\÷Zõ3$g%€≥\ÁA\Èìˆ∏U',1,1,NULL),(8,'praveen','bhadri','praveen.bhadri98@gmail.com',1,'b552eab70ba740b78c13511ba07393b2',_binary '668156d70b3b4c859dd93cb277dcaf5e',_binary 'cøàB\Î∑\›\"t∏V\‘5\Ô\◊≠öã/É·òÆU\›0ø∫	®¿©˝Båßd>Ù±Å˚\Ó\në6^(\Ízv\Œb ‘ΩÇ',2,5,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwcmF2ZWVuLmJoYWRyaTk4QGdtYWlsLmNvbSIsInJvbGUiOjIsImZpcnN0TmFtZSI6InByYXZlZW4iLCJleHAiOjE1NTAwNTIxMTJ9.m90M62Apo7xwQrfToifCwKUHbtKDsMiaKc5fTzvxDCU'),(9,'sonu','bhadri','sonu.bhadri@gmail.com',1,'68d8b410382b43ecb822b2446935b158',_binary '55d8bbf3a4fb440ba841d2f50d799987',_binary '‹ö˘ä\≈≤µIZY≠Ä¶<yÑè¸Ω\0¢d\Ó◊Å£\◊\·kO\Ÿw[\œ/›π©\Ô˛zO\È\‘¸\‘˜à§-\Ê\Ê˚åí49\Õs',1,1,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzb251LmJoYWRyaUBnbWFpbC5jb20iLCJyb2xlIjoxLCJmaXJzdE5hbWUiOiJzb251IiwiZXhwIjoxNTUwMDUyMTU2fQ.PmewyxO5y4uwiZ2n8BPZmtXNPR688fltjOFTEEmEBgI');
/*!40000 ALTER TABLE `Users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TranslatorRoles`
--

DROP TABLE IF EXISTS `TranslatorRoles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TranslatorRoles` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `RoleName` text COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TranslatorRoles`
--

LOCK TABLES `TranslatorRoles` WRITE;
/*!40000 ALTER TABLE `TranslatorRoles` DISABLE KEYS */;
INSERT INTO `TranslatorRoles` VALUES (1,'align'),(2,'translate'),(3,'check');
/*!40000 ALTER TABLE `TranslatorRoles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Assignments`
--

DROP TABLE IF EXISTS `Assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Assignments` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `User_id` int(11) NOT NULL,
  `Organisation_id` int(11) NOT NULL,
  `TranslatorRole_id` int(11) NOT NULL,
  `Books` text COLLATE utf8_bin NOT NULL,
  `Language` text COLLATE utf8_bin NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `User_id` (`User_id`),
  KEY `Organisation_id` (`Organisation_id`),
  KEY `TranslatorRole_id` (`TranslatorRole_id`),
  CONSTRAINT `Assignments_ibfk_1` FOREIGN KEY (`User_id`) REFERENCES `Users` (`ID`),
  CONSTRAINT `Assignments_ibfk_2` FOREIGN KEY (`Organisation_id`) REFERENCES `Organisations` (`ID`),
  CONSTRAINT `Assignments_ibfk_3` FOREIGN KEY (`TranslatorRole_id`) REFERENCES `TranslatorRoles` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Assignments`
--

LOCK TABLES `Assignments` WRITE;
/*!40000 ALTER TABLE `Assignments` DISABLE KEYS */;
INSERT INTO `Assignments` VALUES (5,4,2,1,'mat,mrk,luk','hin-4'),(6,9,5,1,'gen','hin-4'),(7,9,5,1,'mat','urd-5');
/*!40000 ALTER TABLE `Assignments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Organisations`
--

DROP TABLE IF EXISTS `Organisations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Organisations` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `Name` text COLLATE utf8_bin NOT NULL,
  `Address` text COLLATE utf8_bin NOT NULL,
  `Email` varchar(20) COLLATE utf8_bin NOT NULL,
  `Country_code` int(3) NOT NULL,
  `Phone` varchar(15) COLLATE utf8_bin DEFAULT NULL,
  `Approved` tinyint(3) DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Organisations`
--

LOCK TABLES `Organisations` WRITE;
/*!40000 ALTER TABLE `Organisations` DISABLE KEYS */;
INSERT INTO `Organisations` VALUES (1,'Name','Address','Email',0,'0',0),(2,'BCS','Delhi','mail@bcs.com',91,'10000000',0),(3,'BCS1','Bangalore','bcs1@mail.com',91,'1910192029',0),(4,'no_name','no_address','no_email',0,'0',0),(5,'BCS','Delhi','bijob89@gmail.com',32,'999999999',0);
/*!40000 ALTER TABLE `Organisations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-02-12 15:39:30
