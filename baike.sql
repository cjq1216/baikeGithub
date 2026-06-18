/*
 Navicat Premium Dump SQL

 Source Server         : cjq腾讯云-MySQL
 Source Server Type    : MySQL
 Source Server Version : 80045 (8.0.45)
 Source Host           : 162.14.107.126:3307
 Source Schema         : baike

 Target Server Type    : MySQL
 Target Server Version : 80045 (8.0.45)
 File Encoding         : 65001

 Date: 18/06/2026 09:07:53
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for comment
-- ----------------------------
DROP TABLE IF EXISTS `comment`;
CREATE TABLE `comment`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `lemma_id` int NOT NULL,
  `content` varchar(320) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  INDEX `lemma_id`(`lemma_id` ASC) USING BTREE,
  CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `comment_ibfk_2` FOREIGN KEY (`lemma_id`) REFERENCES `lemma` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of comment
-- ----------------------------
INSERT INTO `comment` VALUES (1, 1, 1, '888888', '2026-06-15 05:59:51');

-- ----------------------------
-- Table structure for lemma
-- ----------------------------
DROP TABLE IF EXISTS `lemma`;
CREATE TABLE `lemma`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `updated_at` datetime NOT NULL,
  `view_count` int NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of lemma
-- ----------------------------
INSERT INTO `lemma` VALUES (1, '123', '<p><font size=\"6\">第一</font></p><p>这里是第一</p><p><font color=\"#800080\" size=\"6\">第二</font></p><p><font color=\"#ff0000\" size=\"4\">竣棋超神了</font></p><p><font color=\"#0000ff\" size=\"6\">第三</font></p><p><font color=\"#ff00ff\" size=\"5\">加个鸡腿</font></p><p><br></p>', '2026-06-15 05:59:45', 1);
INSERT INTO `lemma` VALUES (2, '啦啦啦1我是竣棋呀', '<p><font color=\"#880000\" size=\"4\">完全不想睡觉</font></p><p><font size=\"6\">爽到飞起</font></p><p><font color=\"#ff0000\" size=\"5\">一句话写完了查询</font><br></p><p><br></p>', '2026-06-15 05:59:30', 1);
INSERT INTO `lemma` VALUES (3, 'hh哈哈哈641好厉害哦', '<p><font size=\"6\">本学期第四次看日出</font></p><p><font size=\"4\"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size=\"6\">打代码真他妈精神</font></p><p><font size=\"4\"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size=\"6\">明天就回家了好开心</font></p><p><font size=\"4\"><span>明天的意思是今天的第二天；也泛指未来、希望，如\"孩子是祖国的明天\"。</span></font></p><p><br></p>', '2026-06-12 07:16:00', 0);
INSERT INTO `lemma` VALUES (4, '分工-张芳淋-前端设计与实现，配置运行环境', '<p><font size=\"6\">本学期第四次看日出</font></p><p><font size=\"4\"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size=\"6\">打代码真他妈精神</font></p><p><font size=\"4\"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size=\"6\">明天就回家了好开心</font></p><p><font size=\"4\"><span>明天的意思是今天的第二天；也泛指未来、希望，如\"孩子是祖国的明天\"。</span></font></p><p><br></p>', '2026-06-12 07:16:00', 0);
INSERT INTO `lemma` VALUES (5, '苏庭轩-分工-前端实现与后台开发', '<p><font size=\"6\">本学期第四次看日出</font></p><p><font size=\"4\"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size=\"6\">打代码真他妈精神</font></p><p><font size=\"4\"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size=\"6\">明天就回家了好开心</font></p><p><font size=\"4\"><span>明天的意思是今天的第二天；也泛指未来、希望，如\"孩子是祖国的明天\"。</span></font></p><p><br></p>', '2026-06-12 07:16:00', 0);
INSERT INTO `lemma` VALUES (6, '刘中琦-分工-数据库设计、后台数据库操作', '<p><font size=\"6\">本学期第四次看日出</font></p><p><font size=\"4\"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size=\"6\">打代码真他妈精神</font></p><p><font size=\"4\"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size=\"6\">明天就回家了好开心</font></p><p><font size=\"4\"><span>明天的意思是今天的第二天；也泛指未来、希望，如\"孩子是祖国的明天\"。</span></font></p><p><br></p>', '2026-06-12 07:16:00', 0);
INSERT INTO `lemma` VALUES (7, '楚竣棋-后台逻辑设计与实现，服务器管理与维护-分工', '<p><font size=\"6\">来看日出</font></p><p><font size=\"4\"><span>日出，指太阳初升出地平线或最初看到的太阳的出现。一般是指太阳由东方的地平线徐徐升起的时间，而确实的定义为日面刚从地平线出现的一刹那，而非整个日面离开地平线。</span></font></p><p><font size=\"6\">打代码真开心</font></p><p><font size=\"4\"><span>国内外有一种网络兼职数据录入工作，叫做：打码（captcha human bypass），很多在网络上找钱的朋友或多或少都接触过这个名词，但是知道此任务由来、渊源的确是为数不多。</span></font></p><p><font size=\"6\">我爱软件架构</font></p><p><font size=\"4\"><span>明天的意思是今天的第二天；也泛指未来、希望，如\"孩子是祖国的明天\"。</span></font></p><p><br></p>', '2026-06-12 07:16:00', 0);

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `is_admin` tinyint(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, 'a', 'scrypt:32768:8:1$jUNfTt1WcVD7KqgN$448d315a877f06c1f174ef9fc010b6f75f229eeb41cb9f8368a454b8fa93485e685e9bab74e5dd33056aff6d66676f90ae68c8d30b5838bf6ddbb198cb428751', 1);

SET FOREIGN_KEY_CHECKS = 1;
