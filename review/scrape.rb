require 'open-uri'
require 'csv'
require 'active_support/all'
require 'selenium-webdriver'
require 'optparse'

class ScrapeJalanReview
  URL = 'https://www.jalan.net/yad%s/kuchikomi/'

  def initialize(yado_no:)
    options = Selenium::WebDriver::Chrome::Options.new(
      args: ['--headless', '--disable-gpu', 'window-size=1280x800'],
    )
    @driver = Selenium::WebDriver.for :chrome, options: options
    @driver.navigate.to(sprintf(URL, yado_no))
    @wait = Selenium::WebDriver::Wait.new(timeout: 20)
  end

  def scrape
    list = []
    loop do
      @wait.until { @driver.find_element(:xpath, "//div[contains(@class, 'user-kuchikomi')]").displayed? }
      @driver.find_elements(:xpath, "//div[contains(@class, 'user-kuchikomi')]").map do |node|
        attrs = node.find_element(:xpath, ".//p[@class='user-name']").text.split('/')
        sex = attrs[0].split(' ').last
        age = attrs[1] ? attrs[1].split("\n").first.strip : ''
        date = node.find_element(:xpath, ".//p[@class='post-date']").text.split('：').last
        comment_lines = node.find_element(:xpath, "p[@class='text']").text.strip.split("\n")
        title = comment_lines.first
        body = comment_lines[1..-1].join(' ')
        scores = node.find_elements(:xpath, "div[@class='rate']/dl/dd").map { |dd| dd.text }
        list.push([sex, age, date, title, body] + scores)
      end

      break if @driver.find_elements(:xpath, "//nav/a[@class='next']").size == 0

      next_link = @driver.find_element(:xpath, "//nav/a[@class='next']")
      next_link.location_once_scrolled_into_view
      puts "page: #{next_link.text}"
      next_link.click
      sleep(0.5)
    end
    @driver.quit

    list
  end
end

params = ARGV.getopts('', 'yado_no:').symbolize_keys

if params[:yado_no].blank?
  puts "usage: ruby scrape.rb --yado_no 12341234"
  exit
end

review = ScrapeJalanReview.new(yado_no: params[:yado_no])
list = review.scrape

CSV.open("kuchikomi_#{params[:yado_no]}.csv", "w") do |io|
  list.each { |row| io.puts(row) }
end