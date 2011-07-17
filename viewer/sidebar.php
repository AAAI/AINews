    <div id="sidebar">
            <ul>
                <li>
                    <h2>AI News</h2>
                    <ul>
                        <li><a href="index.php">Home</a></li>
                        <li><a href="news.php">
                            <?php if($type=="news"):?>
                            <b>Recent news</b>
                            <?php else: ?>
                            Recent news
                            <?php endif; ?>
                            </a></li>
                        <li><a href="news.php?type=corpus">
                            <?php if($type=="corpus"):?>
                            <b>Training corpus</b>
                            <?php else: ?>
                            Training corpus
                            <?php endif; ?>
                        </a></li>
                    </ul>
                </li>
            </ul>
        </div>
        <!-- end #sidebar -->
