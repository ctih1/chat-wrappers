package fi.ctih1.chat;

import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.scheduler.BukkitRunnable;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Objects;

public class MessageListener implements Listener {
    static Chat instance = Chat.getInstance();

    private void sendMessage(Player player, String message) {
        new BukkitRunnable() {
            @Override
            public void run() {
                player.sendMessage(message);
            }
        }.runTaskLater(instance, 10L);
    }

    private void sendRequest(Player player, String message) {
        try {
            URL url = new URL("http://192.168.32.88:3001/api/chat");
            HttpURLConnection con = (HttpURLConnection) url.openConnection();
            con.setRequestMethod("POST");
            con.setRequestProperty("Content-Type", "application/json");
            con.setConnectTimeout(5000);
            con.setReadTimeout(5000);
            con.setDoOutput(true);

            HashMap<String, String> bodyMap = new HashMap<String, String>();
            bodyMap.put("source", "minecraft");
            bodyMap.put("ip", player.getAddress().toString());
            bodyMap.put("text", message);

            String body = new Gson().toJson(bodyMap);

            try(OutputStream os = con.getOutputStream()) {
                byte[] input = body.getBytes("utf-8");
                os.write(input, 0, input.length);
            }

            int status = con.getResponseCode();
            InputStream in;
            if (status >= 400) {
                in = con.getErrorStream();
            } else {
                in = con.getInputStream();
            }
            if(status == 200) {
                sendMessage(player, ChatColor.GREEN + "Sent message! ^^");
                player.playSound(player.getLocation(), Sound.BLOCK_NOTE_BLOCK_PLING, 1.0f, 1.0f);
            } else {
                try(BufferedReader br = new BufferedReader(
                        new InputStreamReader(in, "utf-8"))) {
                    StringBuilder response = new StringBuilder();
                    String responseLine = null;
                    while ((responseLine = br.readLine()) != null) {
                        response.append(responseLine.trim());
                    }
                    JsonObject obj = JsonParser.parseString(response.toString()).getAsJsonObject();
                    sendMessage(player, ChatColor.RED + String.valueOf(obj.get("message")));
                    player.playSound(player.getLocation(), Sound.ENTITY_CAT_HISS, 1.0f, 1.0f);
                }
            }
            instance.playerMessageMap.remove(player.getUniqueId());
        } catch (MalformedURLException e) {
            e.printStackTrace();
            System.out.println("???????");
            sendMessage(player, ChatColor.RED + "Something went wrong");
        } catch (IOException e) {
            e.printStackTrace();
            sendMessage(player, ChatColor.RED + "API connection failed");
        }
    }

    @EventHandler
    public void onPlayerChat(AsyncPlayerChatEvent event) {
        new BukkitRunnable() {
            @Override
            public void run() {
                Player player = event.getPlayer();
                String message = event.getMessage();

                if(!instance.playerMessageMap.containsKey(player.getUniqueId())) {
                    sendMessage(player, "\"Aye aye Captain, message received.\n " + ChatColor.BOLD + "Do you want to send that? (yes / no)\"");

                    instance.playerMessageMap.put(player.getUniqueId(), message);
                    return;
                }

                if(!(message.equals("yes") || message.equals("no"))) {
                    sendMessage(player, "Invalid to response to a yes/no question bruh\n" + ChatColor.RED + "Cancelled message.");
                    instance.playerMessageMap.remove(player.getUniqueId());
                    return;
                }

                if(message.equals("yes")) {
                    sendRequest(player, instance.playerMessageMap.get(player.getUniqueId()));
                } else {
                    sendMessage(player, ChatColor.RED +"Cancelled message");
                    instance.playerMessageMap.remove(player.getUniqueId());
                }

            }
        }.runTask(instance);
    }
}
