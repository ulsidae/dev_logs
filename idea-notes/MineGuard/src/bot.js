const mineflayer = require('mineflayer')
const { pathfinder, Movements, goals } =
  require('mineflayer-pathfinder')

const SERVER_HOST = ' ' // SERVER IPv4 address
const SERVER_PORT = 8080

const BOT_USERNAME = ' '
const TARGET_USERNAME = ' '

const bot = mineflayer.createBot({
  host: SERVER_HOST,
  port: SERVER_PORT,

  username: BOT_USERNAME,
  auth: 'microsoft'
})

bot.loadPlugin(pathfinder)

bot.once('spawn', () => {
  console.log('Guardian connected!')
  console.log(`Bot username: ${bot.username}`)
  console.log(`Minecraft version: ${bot.version}`)

  const mcData = require('minecraft-data')(bot.version)
  const movements = new Movements(bot, mcData)

  bot.pathfinder.setMovements(movements)

  const target = bot.players[TARGET_USERNAME]

  if (!target || !target.entity) {
    console.log(`Player not found: ${TARGET_USERNAME}`)
    return
  }

  console.log(`Following ${TARGET_USERNAME}`)

  bot.pathfinder.setGoal(
    new goals.GoalFollow(target.entity, 4),
    true
  )
})

bot.on('error', error => {
  console.error('Bot error:', error)
})

bot.on('kicked', reason => {
  console.log('Bot kicked:', reason)
})

bot.on('end', () => {
  console.log('Bot disconnected.')
})
